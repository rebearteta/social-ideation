import datetime
import logging
import hashlib
import hmac
import json
import traceback

from app.models import SocialNetworkApp, SocialNetworkAppUser, Initiative, Idea, Campaign
from app.sync import save_sn_post, publish_idea_cp, save_sn_comment, publish_comment_cp, save_sn_vote, \
                     delete_post, delete_comment, delete_vote, is_user_community_member
from app.utils import get_timezone_aware_datetime, calculate_token_expiration_time
from connectors.social_network import Facebook
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.translation import activate, ugettext as _

from .forms import SignInForm

logger = logging.getLogger(__name__)


def _process_post(post_id, update, fb_app, u_datetime):
    template_url_post = 'https://www.facebook.com/{}/posts/{}'

    if not 'message' in update.keys() or not update['message'].strip():
        # Posts without text are ignored
        return None
    url = template_url_post.format(post_id.split('_')[0],post_id.split('_')[1])
    post = {'id': post_id, 'text': update['message'], 'title': '',
            'user_info': {'name': update['sender_name'], 'id': str(update['sender_id'])},
            'url': url, 'datetime': u_datetime, 'positive_votes': 0, 'negative_votes': 0,
            'comments': 0}
    ret_data = save_sn_post(fb_app, post)
    if ret_data: publish_idea_cp(ret_data['idea'])


def _process_comment(comment_id, comment_raw, fb_app, c_datetime):
    if not comment_raw['message'].strip():
        # Comments without text are ignored
        return None
    if comment_raw['post_id'] == comment_raw['parent_id']:
        parent_type = 'post'
    else:
        parent_type = 'comment'
    comment = {'id': comment_id, 'text': comment_raw['message'],
               'user_info': {'name': comment_raw['sender_name'], 'id': str(comment_raw['sender_id'])},
               'datetime': c_datetime, 'positive_votes': 0, 'negative_votes': 0, 'url': None,
               'parent_type': parent_type, 'parent_id': comment_raw['parent_id'], 'comments': 0}
    ret_data = save_sn_comment(fb_app, comment)
    if ret_data: publish_comment_cp(ret_data['comment'])


def _generate_like_id(like_raw):
    return like_raw['parent_id'].split('_')[1]+'_'+str(like_raw['sender_id'])


def _process_like(like_raw, fb_app, l_datetime):
    if like_raw['post_id'] == like_raw['parent_id']:
        parent_type = 'post'
    else:
        parent_type = 'comment'
    like = {'id': _generate_like_id(like_raw),
            'user_info': {'id': str(like_raw['sender_id']), 'name': like_raw['sender_name']},
            'parent_type': parent_type, 'parent_id': like_raw['parent_id'], 'value': 1,
            'datetime': l_datetime}
    save_sn_vote(fb_app, like)


def _process_update(fb_app, update, u_datetime):
    if update['item'] == 'post' or update['item'] == 'share' or update['item'] == 'status':
        post_id = str(update['post_id'])
        if update['verb'] == 'add':
            _process_post(post_id, update, fb_app, u_datetime)
        elif update['verb'] == 'remove':
            delete_post(post_id)
        else:
            logger.info('Action type {} are ignored'.format(update['verb']))
    elif update['item'] == 'comment':
        comment_id = str(update['comment_id'])
        if update['verb'] == 'add':
            _process_comment(comment_id, update, fb_app, u_datetime)
        elif update['verb'] == 'remove':
            delete_comment(comment_id)
        else:
            logger.info('Action type {} are ignored'.format(update['verb']))
    elif update['item'] == 'like':
        if update['verb'] == 'add':
            _process_like(update, fb_app, u_datetime)
        elif update['verb'] == 'remove':
            delete_vote(_generate_like_id(update))
        else:
            logger.info('Action type {} are ignored'.format(update['verb']))
    else:
        # Ignore the rest
        logger.info('Updates of type {} are ignored'.format(update['item']))


def _get_datetime(raw_datetime):
    try:
        dt = datetime.datetime.fromtimestamp(raw_datetime)
        if timezone.is_naive(dt):
            return get_timezone_aware_datetime(dt).isoformat()
        else:
            return dt.isoformat()
    except Exception as e:
        logger.warning('Error when trying to calculate the update datetime. Reason: {}'.format(e))
        logger.warning(traceback.format_exc())
        return None

def _encode_payload(payload):
    try:
        if type(payload) == type(' '.decode()):
            return payload.encode()
        else:
            return payload
    except Exception as e:
        logger.warning('Error when trying to encode a payload. Reason: {}'.format(e))
        logger.warning(traceback.format_exc())
        return None


def _process_post_request(fb_app, exp_signature, payload):
    # Save the current signature
    fb_app.last_real_time_update_sig = str(exp_signature)
    fb_app.save()
    req_json = json.loads(payload)
    req_json = _encode_payload(req_json)
    if req_json['object'] == fb_app.object_real_time_updates:
        entries = req_json['entry']
        for entry in entries:
            if entry['id'] == fb_app.page_id:
                e_datetime = _get_datetime(entry['time'])
                if e_datetime:
                    changes = entry['changes']
                    for change in changes:
                        if change['field'] == fb_app.field_real_time_updates:
                            _process_update(fb_app, change['value'], e_datetime)
                        else:
                            logger.info('Unknown update field. Expected: {}, received: {}'.
                                        format(fb_app.field_real_time_updates, change['field']))
            else:
                logger.info('Unknown page id {}. Update will be ignored'.format(entry['id']))
    else:
        logger.info('Unknown update objects. Expected: {}, received: {}'.
                    format(fb_app.object_real_time_updates, req_json['object']))


def _calculate_signature(app_secret, payload):
    try:
        return 'sha1=' + hmac.new(str(app_secret), msg=unicode(str(payload)), digestmod=hashlib.sha1).hexdigest()
    except Exception as e:
        logger.warning('Signature could not be generated. Reason: {}'.format(e))
        logger.warning(traceback.format_exc())
        return None


def _get_facebook_app():
    apps = SocialNetworkApp.objects.all()
    for app in apps:
        if app.connector.name.lower() == 'facebook':
            return app
    return None

@csrf_exempt
def fb_real_time_updates(request):
    fb_app = _get_facebook_app()
    if fb_app:
        if request.method == 'GET':
            challenge = request.GET.get('hub.challenge')
            token = request.GET.get('hub.verify_token')
            if fb_app.token_real_time_updates == token:
                return HttpResponse(challenge)
        elif request.method == 'POST':
            req_signature = request.META.get('HTTP_X_HUB_SIGNATURE')
            exp_signature = _calculate_signature(fb_app.app_secret, request.body)
            if req_signature == exp_signature and \
               not exp_signature == fb_app.last_real_time_update_sig:
                # I'm comparing the current signature against the last one
                # to discard duplicates that seem to arrive consecutively
                _process_post_request(fb_app, exp_signature, request.body)
                return HttpResponse()
            else:
                logger.info('The received signature does not correspond to the expected one or '
                            'the request is a duplicate')
    return HttpResponseForbidden()


def is_supported_language(language_code):
    supported_languages = dict(settings.LANGUAGES).keys()
    return language_code in supported_languages


def get_initiative_info():
    # Hardcoded get the first active initiative and the
    # url of the community associated to the first social network
    # where it is executed
    initiative = Initiative.objects.get(active=True)
    return {'initiative_name': initiative.name, 'initiative_url': initiative.url,
            'fb_group_url': initiative.social_network.all()[0].community.url}

def _get_recent_ideas ():
    recent_ideas = Idea.objects.order_by('-datetime')[:3]
    return recent_ideas

def _get_top_ideas ():
    top_ideas = Idea.objects.order_by('-positive_votes')[:3]
    return top_ideas

def _get_campaigns ():
    campaigns = Campaign.objects.all() #Hardcoded for the first initiative
    return campaigns

def index(request):
    # Detect the default language to show the page
    # If the preferred language is supported, the page will be presented in that language
    # Otherwise english will be chosen
    language_to_render = None

    browser_language_code = request.META.get('HTTP_ACCEPT_LANGUAGE', None)

    if browser_language_code:
        languages = [language for language in browser_language_code.split(',') if
                     '=' not in language]
        for language in languages:
            language_code = language.split('-')[0]
            if is_supported_language(language_code):
                language_to_render = language_code
                break

    if not language_to_render:
        activate('en')
    else:
        activate(language_to_render)

    context = get_initiative_info()
    form = SignInForm()
    context['form'] = form
    context['top'] = _get_top_ideas()
    context['recent'] = _get_recent_ideas()
    context['campaigns'] = _get_campaigns()
    return render(request, 'app/index.html', context)

def register(request):
    language_to_render = None

    browser_language_code = request.META.get('HTTP_ACCEPT_LANGUAGE', None)

    if browser_language_code:
        languages = [language for language in browser_language_code.split(',') if
                     '=' not in language]
        for language in languages:
            language_code = language.split('-')[0]
            if is_supported_language(language_code):
                language_to_render = language_code
                break

    if not language_to_render:
        activate('en')
    else:
        activate(language_to_render)

    context = get_initiative_info()
    form = SignInForm()
    context['form'] = form
    return render(request, 'app/register.html', context)

# NOT USED. PROBABLY IT'S GONNA BE DELETED
def process_login(request):
    # return HttpResponse('It works')
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = SignInForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponse('Formulario completado')
        else:
            return HttpResponse('Datos incorrectos')
    else:
        return HttpResponseRedirect('/')

    # if a GET (or any other method) we'll create a blank form

def _get_initiative_fb_app(initiative_url):
    initiative = Initiative.objects.get(url=initiative_url)
    for snapp in initiative.social_network.all():
        connector = snapp.connector
        if connector.name.lower() == 'facebook':  # Take the Facebook app used to execute the initiative on this sn
            return snapp
    return None


def _save_user(user_id, access_token, initiative_url, type_permission, demo_data):
    fb_app = _get_initiative_fb_app(initiative_url)
    if fb_app:
        ret_token = Facebook.get_long_lived_access_token(fb_app.app_id, fb_app.app_secret,
                                                         access_token)
        try:
            user = SocialNetworkAppUser.objects.get(external_id=user_id)
            user.access_token = ret_token['access_token']
            user.access_token_exp = calculate_token_expiration_time(ret_token['expiration'])
            if type_permission == 'write':
                user.write_permissions = True
            else:
                user.read_permissions = True
            user.save()
        except SocialNetworkAppUser.DoesNotExist:
            #Creamos un ParticipaUser con demo_data. => creamos el snapp user normal => asociamos el snapp al participauser
            user_fb = Facebook.get_info_user(fb_app, user_id, access_token)
            new_app_user = {'email': user_fb['email'].lower(), 'snapp': fb_app, 'access_token': ret_token['access_token'],
                            'access_token_exp': calculate_token_expiration_time(ret_token['expiration']),
                            'external_id': user_id}
            if type_permission == 'write':
                new_app_user.update({'write_permissions': True})
            else:
                new_app_user.update({'read_permissions': True})
            if 'name' in user_fb.keys():
                new_app_user.update({'name': user_fb['name']})
            if 'url' in user_fb.keys():
                new_app_user.update({'url': user_fb['url']})
            user = SocialNetworkAppUser(**new_app_user)
            user.save()
    else:
        logger.warning('It could not be found the facebook app used to execute '
                       'the initiative {}'.format(initiative_url))


def _get_demo_data(request):
    name = request.GET.get('name')
    age = request.GET.get('age')
    sex = request.GET.get('sex')
    email = request.GET.get('email')
    city = request.GET.get('city')
    demo_data = {'name':name, 'age':age, 'sex':sex, 'email':email, 'city':city}
    if (name!=None and email!=None):
    	return demo_data
    else:
	return None


def login_fb(request):
    access_token = request.GET.get('access_token')
    user_id = request.GET.get('user_id')
    initiatiative_url = request.GET.get('initiative_url')
    demo_data = _get_demo_data(request)
    _save_user(user_id, access_token, initiatiative_url, 'read', demo_data)
    return redirect('/app/register?wr_perm=True')

"""
def _save_IS_user(initiative_url, demo_data):
    #Si todos los campos estan correctos creo un ParticipaUser
    #No le asocio Sanppuser porque se registro con IS
    #Creo un cookie con su id y su correo tal vez para usarla en check_participa_user?
    try:
        user = IdeaScaleUser.objects.get(external_id=use)
        user.access_token = ret_token['access_token']
        user.access_token_exp = calculate_token_expiration_time(ret_token['expiration'])
            if type_permission == 'write':
                user.write_permissions = True
            else:
                user.read_permissions = True
            user.save()
        except SocialNetworkAppUser.DoesNotExist:
            user_fb = Facebook.get_info_user(fb_app, user_id, access_token)
            new_app_user = {'email': user_fb['email'].lower(), 'snapp': fb_app, 'access_token': ret_token['access_token'],
                            'access_token_exp': calculate_token_expiration_time(ret_token['expiration']),
                            'external_id': user_id}
            #new demographic data added
            #if demo_data:
            #    new_app_user.update({'age':demo_data['age'], 'city':demo_data['city'], 'sex':demo_data['sex']})
            if type_permission == 'write':
                new_app_user.update({'write_permissions': True})
            else:
                new_app_user.update({'read_permissions': True})
            if 'name' in user_fb.keys():
                new_app_user.update({'name': user_fb['name']})
            if 'url' in user_fb.keys():
                new_app_user.update({'url': user_fb['url']})
            user = SocialNetworkAppUser(**new_app_user)
            user.save()
    else:
        logger.warning('It could not be found the facebook app used to execute '
                       'the initiative {}'.format(initiative_url))

"""
def login_IS(request):
    initiative_url = request.GET.get('initiative_url')
    demo_data = _get_demo_data(request)
    #_save_IS_user() ## After retrieving the data a new IS_user object should be created and saved
    # After the new user is created in our DB a register-confirmation mail must be sent through the API
    # a session value (cookie) should be set here probably to recognize this user.
    
    #return redirect(initiative_url)
    return HttpResponse('We have sent you a confirmation mail. Please verify to join the IdeaScale Initiative ' + str(initiative_url) + str(demo_data)) #just for debugging

def check_user(request): #puede que le agregue otro parametro que me diga si el id es de FB o de IS
    user_id = request.GET.get('user_id')
    try:
        msg_logged = _('Congrats!, You are already logged into') + ' <b>Social Ideation App</b>. '
        msg_group = _('{}group{}').format('<a href="{}" target="_blank"><u>','</u></a>')
        msg_join = _('Join the ')
        msg_ini = _('of the initiative to start participate from Facebook')
        user = SocialNetworkAppUser.objects.get(external_id=user_id)
        # Taking (hardcoded) the first active initiative where the user participate in
        fb_app = user.snapp
        for initiative in fb_app.initiative_set.all():
            if initiative.active:
                msg_group = msg_group.format(initiative.social_network.all()[0].community.url)
                if not user.read_permissions:
                    return HttpResponse()
                if not user.write_permissions:
                    msg_give_write_perm = _('Please consider allowing the app the permission to post '
                                            'on your behalf inside the Facebook')
                    msg_ini_short = _('of the initiative (step 3 below)')
                    msg = msg_logged + msg_give_write_perm + ' ' + msg_group + ' ' + msg_ini_short
                elif not is_user_community_member(fb_app, user):
                    msg = msg_logged + msg_join + msg_group + ' ' + msg_ini
                else:
                    msg_get_in_group = _('Get into the')
                    msg = msg_logged + msg_get_in_group + ' ' + msg_group + ' ' + msg_ini
                return HttpResponse(msg)
        return HttpResponse(msg_logged)
    except SocialNetworkAppUser.DoesNotExist:
        return HttpResponse()


def write_permissions_fb(request):
    access_token = request.GET.get('access_token')
    user_id = request.GET.get('user_id')
    initiatiative_url = request.GET.get('initiative_url')
    _save_user(user_id, access_token, initiatiative_url, 'write', None)
    return redirect('/')
