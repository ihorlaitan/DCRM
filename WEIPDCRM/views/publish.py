# coding=utf-8

"""
DCRM - Darwin Cydia Repository Manager
Copyright (C) 2017  WU Zheng <i.82@me.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import unicode_literals

import os
import urllib

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.decorators.cache import cache_page
from django.views.static import serve

from WEIPDCRM.models.version import Version
from preferences import preferences


def package_file_fetch(request, package_id):
    pref = preferences.Setting
    pkg = Version.objects.get(id=int(package_id))
    if not pkg:
        return HttpResponseNotFound()
    file_path = os.path.join(settings.MEDIA_ROOT, pkg.storage.name)
    if not os.path.exists(file_path):
        return HttpResponseNotFound()
    if pref.download_cydia_only:
        if 'HTTP_X_UNIQUE_ID' not in request.META:
            return HttpResponseBadRequest()
    request_path = pkg.storage.name
    request_url = pkg.get_external_storage_link()
    pkg.download_times = pkg.download_times + 1
    pkg.save()
    if pref.redirect_resources == 1:
        # Redirect URLs
        return redirect(request_url)
    elif pref.redirect_resources == 2:
        # Redirect to WEB server
        response = HttpResponse()
        if pref.web_server == 0:
            response['X-Accel-Redirect'] = request_url
        elif pref.web_server == 1:
            # You may set Send File Path to settings.MEDIA_ROOT
            response['X-sendfile'] = request_path
        elif pref.web_server == 2:
            pass
    else:
        # Return FileResponse By Reading Static File
        response = serve(
            request,
            path=request_path,
            document_root=settings.MEDIA_ROOT,
        )
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Transfer-Encoding'] = "binary"
    response['Cache-Control'] = "public, must-revalidate, max-age=0"
    response['Content-Disposition'] = "attachment; filename=\"" + urllib.quote_plus(pkg.base_filename()) + "\""
    return response


@cache_page(300)
def basic_resource_fetch(request, resource_name):
    rename_list = [
        "Release",
        "Release.gpg",
        "Packages",
        "Packages.gz",
        "Packages.bz2",
        "CydiaIcon",
        "CydiaIcon.png"
    ]
    if resource_name not in rename_list:
        return HttpResponseNotFound()
    pref = preferences.Setting
    if pref.active_release is None:
        return HttpResponseNotFound()
    else:
        release_id = str(pref.active_release.id)
    release_root_path = os.path.join(settings.MEDIA_ROOT, "releases", release_id)
    request_path = os.path.join(release_root_path, resource_name)
    if not os.path.exists(request_path):
        return HttpResponseNotFound()
    if pref.download_cydia_only:
        if 'HTTP_X_UNIQUE_ID' not in request.META:
            return HttpResponseBadRequest()
    release_root_url = os.path.join(pref.resources_alias, "releases", release_id)
    request_url = os.path.join(release_root_url, resource_name)
    if pref.redirect_resources == 1:
        # Redirect URLs
        return redirect(request_url)
    elif pref.redirect_resources == 2:
        # Redirect to WEB server
        if pref.web_server == 0:
            response = HttpResponse()
            response['X-Accel-Redirect'] = request_url
            response['Content-Type'] = 'application/octet-stream'
            return response
        elif pref.web_server == 1:
            # TODO: Apache Support
            pass
        elif pref.web_server == 2:
            # TODO: Tomcat Support
            pass
    elif pref.redirect_resources == 0:
        # Return FileResponse By Reading Static File
        request_path = os.path.join("releases", release_id, resource_name)
        return serve(request, path=request_path, document_root=settings.MEDIA_ROOT)
    # or you can just configure WEB server and rewrite package lists directly to files
