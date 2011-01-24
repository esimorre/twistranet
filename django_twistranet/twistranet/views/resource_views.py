import time
import mimetypes
import os
import traceback
import posixpath
import re
import stat
import urllib
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try :
    # python 2.6
    import json
except :
    # python 2.4 with simplejson
    import simplejson as json

from django.template import Context, RequestContext, loader
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseNotModified
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation
from django.utils.http import http_date                 
from django.conf import settings
from django.views.static import was_modified_since
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import ugettext as _

from sorl.thumbnail import default
from django_twistranet.twistranet.models import *
from django_twistranet.twistranet.forms.resource_forms import ResourceForm, ResourceBrowserForm
from django_twistranet.twistranet.lib.decorators import require_access
from django_twistranet.twistranet.lib.log import log
from django_twistranet.twistorage.storage import Twistorage
from django_twistranet.twistranet.lib import utils

from django.conf import settings


def serve(request, path, document_root = None, show_indexes = False, nocache = False):
    """
    Adapted from django.views.static to handle the creation/modification date of the resource's publisher
    instead of only the file's value.
    
    Serve static files below a given point in the directory structure.

    To use, put a URL pattern such as::

        (r'^(?P<path>.*)$', 'django.views.static.serve', {'document_root' : '/path/to/my/files/'})

    in your URLconf. You must provide the ``document_root`` param. You may
    also set ``show_indexes`` to ``True`` if you'd like to serve a basic index
    of the directory.  This index view will use the template hardcoded below,
    but if you'd like to override it, you can create a template called
    ``static/directory_index.html``.
    """

    # Clean up given path to only allow serving files below document_root.
    path = posixpath.normpath(urllib.unquote(path))
    path = path.lstrip('/')
    newpath = ''
    for part in path.split('/'):
        if not part:
            # Strip empty path components.
            continue
        drive, part = os.path.splitdrive(part)
        head, part = os.path.split(part)
        if part in (os.curdir, os.pardir):
            # Strip '.' and '..' in path.
            continue
        newpath = os.path.join(newpath, part).replace('\\', '/')
    if newpath and path != newpath:
        return HttpResponseRedirect(newpath)
    fullpath = os.path.join(document_root, newpath)
    if os.path.isdir(fullpath):
        # if show_indexes:
        #     return directory_index(newpath, fullpath)
        raise Http404("Directory indexes are not allowed here.")
    if not os.path.exists(fullpath):
        raise Http404('"%s" does not exist' % fullpath)
    
    # Respect the If-Modified-Since header.
    statobj = os.stat(fullpath)
    mimetype = mimetypes.guess_type(fullpath)[0] or 'application/octet-stream'
    # XXX TODO: Handle this correctly!!! Disabled to avoid using file mod. time instead of obj mod. time
    if not nocache:
        if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
                                  statobj[stat.ST_MTIME], statobj[stat.ST_SIZE]):
            return HttpResponseNotModified(mimetype=mimetype)
    contents = open(fullpath, 'rb').read()
    response = HttpResponse(contents, mimetype=mimetype)
    response["Last-Modified"] = http_date(statobj[stat.ST_MTIME])
    response["Content-Length"] = len(contents)
    return response



def _getResourceResponse(request, resource, last_modified = None):
    """
    Return the proper HTTP stream for a resource object
    XXX TODO: Handle the last_modified parameter
    """
    # Determinate the appropriate rendering scheme: file or URL
    if resource.resource_url:
        raise NotImplementedError("We yet have to implement resource URLs")
    
    # Resource file: get storage and check if path exists
    elif resource.resource_file:
        path = resource.resource_file.name      # XXX TODO: Handle subdirectories somehow here
        storage = Twistorage()
        if not storage.exists(path):
            raise Http404

    # Neither a file nor a URL? Then it's probably invalid.
    # Maybe we should implement an "alias" type of resource?
    else:
        raise ValueError("Invalid resource: %s" % resource)

    # Return the underlying file, adapt the Last-Modified header as necessary
    return serve(request, path, document_root = storage.location, show_indexes = False, nocache = True)
    
@require_access
def resource_cache(request, cache_path):
    """
    Return a resource by its cache path.
    XXX TODO: HANDLE SECURITY ON THIS
    """
    return serve(request, cache_path, os.path.join(settings.MEDIA_ROOT, "cache"))

@require_access
def resource_by_id(request, resource_id):
    """
    Return a resource by id
    """
    resource = Resource.objects.get(id = resource_id)
    return _getResourceResponse(request, resource)

@require_access
def resource_by_slug(request, slug):
    """
    XXX TODO: Make this more efficient?
    """
    resource = Resource.objects.get(slug = slug)
    return _getResourceResponse(request, resource)

@require_access
def resource_by_slug_or_id(request, slug_or_id):
    """
    Return a resource by its alias or by its id if not found
    """
    try:
        resource = Resource.objects.get(slug = slug_or_id)
    except ObjectDoesNotExist:
        resource = Resource.objects.get(id = slug_or_id)
    return _getResourceResponse(request, resource)
    
@require_access
def resource_by_account(request, account_id, property):
    """
    Fetch a resource by an account attribute.
    """
    account = Account.objects.get(id = account_id)
    resource = getattr(account, property, None)
    if isinstance(resource, Resource):
        return _getResourceResponse(request, resource)
    else:
        # XXX should raise 404 if pty not found
        raise ValueError("Invalid property")
        
@require_access
def resource_by_content(request, content_id, property):
    """
    Fetch a resource by an content attribute.
    """
    content = Content.objects.get(id = content_id)
    resource = getattr(content, property, None)
    if isinstance(resource, Resource):
        return _getResourceResponse(request, resource)
    else:
        # XXX should raise 404 if pty not found
        raise ValueError("Invalid property")

@require_access
def edit_resource(request, resource_id = None):
    """
    Edit the given resource or create a new one if necessary
    """
    # Get basic information
    account = request.user.get_profile()
    if resource_id is not None:
        resource = Resource.objects.get(id = resource_id)
        # XXX TODO: Implement security here.
        # if not resource.can_view:
        #     raise NotImplementedError("Should implement a permission denied exception here")
        # if not resource.can_edit:
        #     raise NotImplementedError("Should redirect to the regular view? or raise a permission denied exception here.")
        # form_entry = form_registry.getFormEntry(content.content_type)
    else:
        # XXX TODO: Check some kind of "can_create_content" permission?
        resource = None
        # form_entry = form_registry.getFormEntry(content_type)

    # Process form
    if request.method == 'POST': # If the form has been submitted...
        if resource:
            form = ResourceForm(request.POST, request.FILES, instance = resource)
        else:
            form = ResourceForm(request.POST, request.FILES)

        if form.is_valid():
            return HttpResponseRedirect(reverse('django_twistranet.views.resource_by_id', args = (resource.id,)))
    else:
        if resource:
            form = ResourceForm(instance = resource.object)
        else:
            form = ResourceForm()

    # Template hapiness
    t = loader.get_template('resource/edit.html')
    c = RequestContext(
        request,
        {
            "account": account,
            "resource": resource,
            "form": form,
        },
        )
    return HttpResponse(t.render(c))

@require_access
def create_resource(request):
    """
    """
    return edit_resource(request)


@require_access
def resource_browser(request):
    """
    A view used to browse and upload resources
    Used by wysiwyg editors
    Based on resource field
    """
    
    params = {}
    params["account"] = request.user.get_profile()
    params["actions"] = ''
    params["site_name"] = utils.get_site_name()
    params["baseline"] = utils.get_baseline()
    params["allow_browser_selection"] = int(request.GET.get('allow_browser_selection', '') or 0 ) 
    form = ResourceBrowserForm()
    params['form'] = form
    template = 'resource/resource_browser_form.html'
    t = loader.get_template(template)
    c = RequestContext(
        request,
        params
        )
    return HttpResponse(t.render(c))


###############################
# Resource Quick Upload views #
###############################


# JS String used inline by resource_quickupload_init template

UPLOAD_JS = """       
    var fillTitles = %(ul_fill_titles)s;
    var auto = %(ul_auto_upload)s;
    var uploadparams = {};
    if (typeof getActivePublisher!='undefined') {
        uploadparams = { 'publisher_id' : getActivePublisher()};
    }
    addUploadFields_%(ul_id)s = function(file, id) {
        var uploader = xhr_%(ul_id)s;
        TwistranetQuickUpload.addUploadFields(uploader, uploader._element, file, id, fillTitles);
    }
    sendDataAndUpload_%(ul_id)s = function() {
        var uploader = xhr_%(ul_id)s;
        TwistranetQuickUpload.sendDataAndUpload(uploader, uploader._element, '%(typeupload)s');
    }    
    clearQueue_%(ul_id)s = function() {
        var uploader = xhr_%(ul_id)s;
        TwistranetQuickUpload.clearQueue(uploader, uploader._element);    
    }    
    onUploadComplete_%(ul_id)s = function(id, fileName, responseJSON) {       
        var uploader = xhr_%(ul_id)s;
        TwistranetQuickUpload.onUploadComplete(uploader, uploader._element, id, fileName, responseJSON);
    }
    createUploader_%(ul_id)s= function(){    
        xhr_%(ul_id)s = new qq.FileUploader({
            element: jQuery('#%(ul_id)s')[0],
            action: '/resource_quickupload_file/',
            params: uploadparams,
            autoUpload: auto,
            onAfterSelect: addUploadFields_%(ul_id)s,
            onComplete: onUploadComplete_%(ul_id)s,
            allowedExtensions: %(ul_file_extensions_list)s,
            sizeLimit: %(ul_xhr_size_limit)s,
            simUploadLimit: %(ul_sim_upload_limit)s,
            template: '<div class="qq-uploader">' +
                      '<div class="qq-upload-drop-area"><span>%(ul_draganddrop_text)s</span></div>' +
                      '<div class="qq-upload-button">%(ul_button_text)s</div>' +
                      '<ul class="qq-upload-list"></ul>' + 
                      '</div>',
            fileTemplate: '<li>' +
                    '<a class="qq-upload-cancel" href="#">&nbsp;</a>' +
                    '<div class="qq-upload-infos"><span class="qq-upload-file"></span>' +
                    '<span class="qq-upload-spinner"></span>' +
                    '<span class="qq-upload-failed-text">%(ul_msg_failed)s</span></div>' +
                    '<div class="qq-upload-size"></div>' +
                '</li>',                      
            messages: {
                serverError: "%(ul_error_server)s",
                typeError: "%(ul_error_bad_ext)s {file}. %(ul_error_onlyallowed)s {extensions}.",
                sizeError: "%(ul_error_file_large)s {file}, %(ul_error_maxsize_is)s {sizeLimit}.",
                emptyError: "%(ul_error_empty_file)s {file}, %(ul_error_try_again_wo)s"
            }            
        });           
    }
    jQuery(document).ready(createUploader_%(ul_id)s); 
"""


# This view is rendering html and is called in ajax
# TODO : call it with a simple include
@require_access
def resource_quickupload(request):
    qu_settings = dict(
        typeupload             = 'File',
        ul_id                  = 'tnuploader', # improve it to get multiple uploader in a same page, change it also in 'resource_quickupload.html'
        ul_file_extensions_list = '[]', #could be ['jpg,'png','gif']
        
        ul_fill_titles         = settings.QUICKUPLOAD_FILL_TITLES and 'true' or 'false',
        ul_auto_upload         = settings.QUICKUPLOAD_AUTO_UPLOAD and 'true' or 'false',
        ul_xhr_size_limit      = settings.QUICKUPLOAD_SIZE_LIMIT and str(settings.QUICKUPLOAD_SIZE_LIMIT*1024) or '0',
        ul_sim_upload_limit    = str(settings.QUICKUPLOAD_SIM_UPLOAD_LIMIT),
        ul_button_text         = _(u'Browse'),
        ul_draganddrop_text    = _(u'Drag and drop files to upload'),
        ul_msg_all_sucess      = _( u'All files uploaded with success.'),
        ul_msg_some_sucess     = _( u' files uploaded with success, '),
        ul_msg_some_errors     = _( u" uploads return an error."),
        ul_msg_failed          = _( u"Failed"),
        ul_error_try_again_wo  = _( u"please select files again without it."),
        ul_error_try_again     = _( u"please try again."),
        ul_error_empty_file    = _( u"This file is empty :"),
        ul_error_file_large    = _( u"This file is too large :"),
        ul_error_maxsize_is    = _( u"maximum file size is :"),
        ul_error_bad_ext       = _( u"This file has invalid extension :"),
        ul_error_onlyallowed   = _( u"Only allowed :"),
        ul_error_server        = _( u"Server error, please contact support and/or try again."),
    )
    qu_script = UPLOAD_JS % qu_settings
    c = Context({ 'qu_script': qu_script, }) 
    t = loader.get_template('resource/resource_quickupload.html')
    return HttpResponse(t.render(c))


@require_access
def resource_quickupload_file(request):
    """
    json view used by quikupload script
    when uploading a file
    return success/error + file infos (url/preview/title ...)
    """               
    msg = {}
    if request.environ.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        file_name = urllib.unquote(request.environ['HTTP_X_FILE_NAME'])
        title = request.GET.get('title', '')
        upload_with = "XHR"        
        try :
            # the solution for sync ajax file upload
            file_data = SimpleUploadedFile(file_name, request.raw_post_data)
        except :
            log.debug("XHR Upload of %s has been aborted" %file_name)
            # not really useful here since the upload block
            # is removed by "cancel" action, but
            # could be useful if someone change the js behavior
            msg = {u'error': u'emptyError'}
    else :
        # MSIE old behavior (classic upload with iframe) >> TODO : tests
        file_data = request.FILES.get("qqfile", None)
        filename = getattr(file_data,'filename', '')
        file_name = filename.split("\\")[-1]
        title = request.POST.get('title', '')
        upload_with = "CLASSIC FORM POST"
        # we must test the file size in this case (because there is no size client test with msie file field)
        if not utils._check_file_size(file_data) :
            log.debug("The file %s is too big, quick iframe upload rejected" % file_name) 
            msg = {u'error': u'sizeError'}

    if file_data and not msg :
        publisher_id = request.GET.get('publisher_id', '')
        # i'm not sure here
        content_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        if content_type in ('image/jpg', 'image/jpeg', 'image/png', 'image/gif') :
            type = 'image'
        else:
            type = 'file'
        if not title :
            # try to split filenames when there's no title to avoid potential css surprises
            title = file_name.split('.')[0].replace('_',' ').replace('-',' ')
        try :
            params = {'resource_file' : file_data, 'title' : title }
            if publisher_id :
                params['publisher'] = Account.objects.get(id = publisher_id)
            new_file = Resource(**params)
            new_file.save() 

            if type== 'image' :
                preview = default.backend.get_thumbnail( new_file.object.image, u'500x500' )
                preview_url = preview.url
                mini = default.backend.get_thumbnail( new_file.object.image, u'100x100', crop ='center top' ) 
                mini_url = mini.url
            else :
                preview_url = mini_url = ''

            msg = {'success': True,
                   'value':        new_file.id,
                   'url' :         new_file.get_absolute_url(),
                   'preview_url' : preview_url,    
                   'mini_url' :    mini_url, 
                   'legend' :      title, 
                   'scope':        publisher_id,
                   'type' :        type,}
        except:            
            msg = {u'error': u'serverError'}
    else:
        msg = {u'error': u'emptyError'}                

    return HttpResponse( json.dumps(msg),
                         mimetype='text/plain')

###############################
# Resource Browser json views #
###############################

@require_access
def resource_by_publisher_json(request, publisher_id):
    """
    return all resources for a publisher id
    as json dict (for images dict contains all thumb urls) 
    """
    # minimal security check
    account = Twistable.objects.getCurrentAccount(request)
    selectable_accounts_ids = [account.id for account in Resource.objects.selectable_accounts(account)]
    request_account = Account.objects.get(id = publisher_id)
    if int(publisher_id) not in selectable_accounts_ids :
        raise SuspiciousOperation("Attempted access to '%s' denied." % request_account.slug)
    
    selection = request.GET.get('selection','')  or 0
    # TODO : use haystack and batch
    files = Resource.objects.filter(publisher=request_account)[:30]
    results = []
    for file in files :
        img = file.object.image
        file_name = img.name
        content_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        if content_type in ('image/jpeg', 'image/jpg', 'image/png', 'image/gif') :
            type = 'image'
        else:
            type = 'file'
        if type == 'image' :
            thumb = default.backend.get_thumbnail( img, u'50x50', crop ='center top' )
            mini = default.backend.get_thumbnail( img, u'100x100', crop ='center top' )
            preview = default.backend.get_thumbnail( img, u'500x500' )
            thumbnail_url = thumb.url        
            mini_url = mini.url
            preview_url = preview.url  
        
        else :
            thumbnail_url = mini_url = preview_url = ''

        is_selected = file.id == (int(selection) or 0)
        result = {
                "url":              file.get_absolute_url(),
                "thumbnail_url":    thumbnail_url,
                "mini_url":         mini_url, 
                "preview_url":      preview_url,
                "id":               file.id,
                "title":            file.title,
                "selected":         is_selected and ' checked="checked"' or '',
                "type":             type,
                }
        results.append(result)
    data = {}
    # TODO : change it for batch
    data['page'] = 1
    data['results'] = results
    data['sizes'] = ((_('Thumbnail cropped'), '100*100'), (_('Medium size'), '500*500'), (_('Full size'), 'full') )
    return HttpResponse( json.dumps(data),
                         mimetype='text/plain')