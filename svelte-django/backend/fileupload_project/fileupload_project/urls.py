"""
URL configuration for fileupload_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from fileupload.views import (
    create_or_select_project,
    upload_file,
    get_project_files,
    get_file_content,
    call_off_discussion,
    check_processing_status,
#    process_status,
    get_or_create_user,
    get_project_members,
    get_online_users,
    create_project_json,
    delete_file
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', get_or_create_user, name='get_or_create_user'),
    path('api/project/', create_or_select_project, name='create_or_select_project'),
    path('api/projects/', create_or_select_project, name='projects'),
    path('api/upload/', upload_file, name='upload_file'),
    path('api/project-files/', get_project_files, name='get_project_files'),
    path('api/file-content/', get_file_content, name='get_file_content'),
    path('api/call-off-discussion/', call_off_discussion, name='call_off_discussion'),  # Ensure this line is present
    path('api/project-members/<str:project_name>/', get_project_members, name='get_project_members'),
    path('api/online-users/', get_online_users, name='get_online_users'),
    path('api/create-project-json/', create_project_json, name='create_project_json'),
    path('api/delete-file/', delete_file, name='delete_file'),
    path('api/check-processing-status/', check_processing_status, name='check_processing_status'),
#    path('api/process-status/', process_status, name='process_status'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
