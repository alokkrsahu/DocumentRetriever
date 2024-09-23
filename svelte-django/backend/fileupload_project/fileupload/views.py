import subprocess
import base64
from pathlib import Path
import os
import json
import mimetypes
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from .models import Project, UploadedFile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.conf import settings
import logging, threading
from django.db import transaction


from django.views.decorators.http import require_http_methods, require_GET, require_POST

logger = logging.getLogger(__name__)

User = get_user_model()

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_file(request):
    file_id = request.GET.get('file_id')
    if not file_id:
        return JsonResponse({'error': 'File ID is required'}, status=400)

    try:
        file = UploadedFile.objects.get(id=file_id)
        file_path = file.file.name
        
        # Delete the file from storage
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
        else:
            logger.warning(f"File not found in storage: {file_path}")

        # Delete the database entry
        file.delete()
        
        return JsonResponse({'message': 'File deleted successfully'})
    except UploadedFile.DoesNotExist:
        logger.error(f"File with id {file_id} not found in database")
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        logger.exception(f"Error deleting file with id {file_id}")
        return JsonResponse({'error': str(e)}, status=500)
        


@csrf_exempt
def get_or_create_user(request):
    if request.method == 'GET':
        profiles_dir = os.path.join(settings.BASE_DIR, 'profiles')
        if not os.path.exists(profiles_dir):
            os.makedirs(profiles_dir)
        usernames = [name for name in os.listdir(profiles_dir) if os.path.isdir(os.path.join(profiles_dir, name))]
        
        # Ensure all folder names have corresponding user entries
        for username in usernames:
            User.objects.get_or_create(username=username)
        
        # Fetch users from the database
        db_users = User.objects.values_list('username', flat=True)
        
        return JsonResponse({'usernames': list(db_users)})
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def create_or_select_project(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        project_name = data.get('project_name')
        
        if not username or not project_name:
            return JsonResponse({'error': 'Username and project name are required'}, status=400)
        
        user, _ = User.objects.get_or_create(username=username)
        
        safe_project_name = "".join(c for c in project_name if c.isalnum() or c in ('-', '_')).lower()
        
        project, created = Project.objects.get_or_create(name=safe_project_name)
        project.members.add(user)
        
        project_path = os.path.join(settings.MEDIA_ROOT, safe_project_name)
        if not os.path.exists(project_path):
            os.makedirs(project_path)
        
        return JsonResponse({
            'message': 'Project created/selected successfully',
            'project_id': project.id,
            'project_name': project.name
        })

    
    elif request.method == 'GET':
        # List all folders in the media directory as projects
        media_dir = settings.MEDIA_ROOT
        logger.info(f"Checking media directory: {media_dir}")
        
        if not os.path.exists(media_dir):
            logger.warning(f"Media directory does not exist: {media_dir}")
            return JsonResponse({'projects': [], 'error': 'Media directory not found'})
        
        project_folders = [name for name in os.listdir(media_dir) if os.path.isdir(os.path.join(media_dir, name))]
        logger.info(f"Found project folders: {project_folders}")
        
        # Ensure all folder names have corresponding project entries
        projects = []
        for folder_name in project_folders:
            project, _ = Project.objects.get_or_create(name=folder_name)
            projects.append({'id': project.id, 'name': project.name})
        
        logger.info(f"Returning projects: {projects}")
        return JsonResponse({'projects': projects})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        username = request.POST.get('username')
        files = request.FILES.getlist('files[]')
        uploaded_files = []

        if not project_id or not username:
            return JsonResponse({'error': 'Project ID and username are required'}, status=400)

        try:
            project = Project.objects.get(id=project_id)
            user = User.objects.get(username=username)
        except (Project.DoesNotExist, User.DoesNotExist):
            return JsonResponse({'error': 'Project or User not found'}, status=404)

        project_folder = os.path.join(settings.MEDIA_ROOT, project.name, 'documents')
        os.makedirs(project_folder, exist_ok=True)

        for uploaded_file in files:
            file_path = os.path.join(project_folder, uploaded_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            file_instance = UploadedFile(
                file=file_path,
                project=project,
                uploaded_by=user,
            )
            file_instance.save()

            uploaded_files.append({
                'id': file_instance.id,
                'name': file_instance.file_name,
                'path': file_instance.file.url,
                'size': file_instance.file_size,
                'type': file_instance.file_type
            })

        logger.debug(f"Files uploaded to: {project_folder}")
        logger.debug(f"Uploaded files: {[f['name'] for f in uploaded_files]}")

        return JsonResponse({
            'message': 'Files uploaded successfully',
            'files': uploaded_files
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)





@csrf_exempt
def get_project_files(request):
    if request.method == 'GET':
        project_id = request.GET.get('project_id')
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)
        
        files = UploadedFile.objects.filter(project=project).values('id', 'file', 'uploaded_at', 'uploaded_by__username')
        return JsonResponse({'files': list(files)})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def get_file_content(request):
    if request.method == 'GET':
        file_path = request.GET.get('file_path')
        if file_path and default_storage.exists(file_path):
            with default_storage.open(file_path, 'rb') as file:
                content = file.read().decode('utf-8')
            return JsonResponse({'content': content})
        
        return JsonResponse({'error': 'File not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def create_project_json(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        project_id = data.get('project_id')
        
        if not username or not project_id:
            return JsonResponse({'error': 'Username and project ID are required'}, status=400)
        
        try:
            user = User.objects.get(username=username)
            project = Project.objects.get(id=project_id)
        except (User.DoesNotExist, Project.DoesNotExist):
            return JsonResponse({'error': 'User or Project not found'}, status=404)
        
        json_content = {
            "project_created": project.created_at.isoformat(),
            "project_name": project.name,
            "members": list(project.members.values_list('username', flat=True))
        }
        
        json_file_path = os.path.join(settings.MEDIA_ROOT, project.name, f"{project.name}.json")
        with open(json_file_path, 'w') as f:
            json.dump(json_content, f)
        
        return JsonResponse({'message': 'Project JSON created successfully'})
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)








@csrf_exempt
@require_http_methods(["DELETE"])
def delete_file(request):
    file_id = request.GET.get('file_id')
    if not file_id:
        return JsonResponse({'error': 'File ID is required'}, status=400)

    try:
        file = UploadedFile.objects.get(id=file_id)
        file_path = file.file.name
        
        # Delete the file from storage
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
        else:
            logger.warning(f"File not found in storage: {file_path}")

        # Delete the database entry
        file.delete()
        
        return JsonResponse({'message': 'File deleted successfully'})
    except UploadedFile.DoesNotExist:
        logger.error(f"File with id {file_id} not found in database")
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        logger.exception(f"Error deleting file with id {file_id}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def get_file_content(request):
    if request.method == 'GET':
        file_path = request.GET.get('file_path')
        if file_path and default_storage.exists(file_path):
            file_type, _ = mimetypes.guess_type(file_path)
            
            with default_storage.open(file_path, 'rb') as file:
                file_content = file.read()
                
            if file_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                             'application/pdf',
                             'image/jpeg',
                             'image/png',
                             'image/gif']:
                encoded_content = base64.b64encode(file_content).decode('utf-8')
                return JsonResponse({
                    'content': encoded_content,
                    'type': file_type,
                    'name': os.path.basename(file_path)
                })
            elif file_type in ['text/plain', 'text/csv']:
                try:
                    content = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    content = file_content.decode('latin-1')  # Fallback encoding
                return JsonResponse({
                    'content': content,
                    'type': file_type
                })
            else:
                return JsonResponse({
                    'message': f"Cannot display content of {file_type} files directly. Please download to view.",
                    'type': file_type
                })
        
        return JsonResponse({'error': 'File not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@require_POST
def call_off_discussion(request):
    logger.debug("call_off_discussion function called")
    try:
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")
        project_name = data.get('project_name')
        username = data.get('username')
        action = data.get('action', 'call_off')
        
        logger.debug(f"Project: {project_name}, User: {username}, Action: {action}")

        if not project_name or not username:
            return JsonResponse({'error': 'Project name and username are required'}, status=400)

        try:
            project = Project.objects.get(name=project_name)
            logger.debug(f"Found project: {project}")
        except Project.DoesNotExist:
            logger.error(f'Project not found: {project_name}')
            return JsonResponse({'error': f'Project not found: {project_name}'}, status=404)

        if action == 'process_docs':
            if not project.is_processing_complete:
                logger.debug("Starting document processing")
                # Start the document processing in a separate thread
                threading.Thread(target=process_project_documents, args=(project.id,)).start()
                return JsonResponse({'message': 'Document processing started', 'status': 'processing'})
            else:
                logger.debug("Documents already processed")
                return JsonResponse({'message': 'Files are ready', 'status': 'completed', 'processed_location': project.processed_location})
        elif action == 'call_off':
            if project.is_processing_complete:
                # Run the analysis command
                analysis_output = run_analysis(project)
                if analysis_output:
                    return JsonResponse({'message': 'Call off discussion complete', 'status': 'completed', 'results': analysis_output})
                else:
                    return JsonResponse({'error': 'Analysis failed'}, status=500)
            else:
                return JsonResponse({'message': 'Files are not processed yet', 'status': 'not_ready'})
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        logger.exception("Unexpected error in call_off_discussion")
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)





@require_GET
def check_processing_status(request):
    project_name = request.GET.get('project_name')
    if not project_name:
        return JsonResponse({'error': 'Project name is required'}, status=400)

    try:
        project = Project.objects.get(name=project_name)
        return JsonResponse({'status': 'completed' if project.is_processing_complete else 'processing', 'processed_location': project.processed_location})
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)



@transaction.atomic
def process_project_documents(project_id):
    logger.debug(f"process_project_documents called with project_id: {project_id}")
    try:
        project = Project.objects.get(id=project_id)
        project_path = os.path.join(settings.MEDIA_ROOT, project.name)
        documents_path = os.path.join(project_path, 'documents')
        logger.debug(f"Processing project: {project.name}, Documents Path: {documents_path}")
        logger.debug(f"Files in documents path: {os.listdir(documents_path)}")

        output_dir = os.path.join(project_path, 'sys', 'temp')
        os.makedirs(output_dir, exist_ok=True)

        initial_processor_command = [
            'python3',
            os.path.join(settings.BASE_DIR, 'retrievals', 'documentretriever', 'process.py'),
            documents_path,
            '--min-chars', '100',
            '--min-words', '30',
            '--output-dir', output_dir
        ]

        
        logger.debug(f"Running command: {' '.join(initial_processor_command)}")
        try:
            process = subprocess.run(initial_processor_command, check=True, capture_output=True, text=True)
            logger.debug(f"Process output: {process.stdout}")
            logger.debug(f"Process error: {process.stderr}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running initial processor: {e}")
            logger.error(f"Process output: {e.output}")
            logger.error(f"Process error: {e.stderr}")
            return

        
        logger.debug(f"Process output: {process.stdout}")
        logger.debug(f"Process error: {process.stderr}")

        output_lines = process.stdout.strip().split('\n')
        output_file_path = None
        for line in output_lines:
            if line.startswith("Files have been saved to"):
                output_file_path = line.split("Files have been saved to")[-1].strip()
                break
        
        if not output_file_path or not os.path.exists(output_file_path):
            logger.error(f"Output file not found: {output_file_path}")
            return

        logger.debug(f"Output file path: {output_file_path}")
        if os.path.exists(output_file_path):
            logger.debug(f"extracted_data.json size: {os.path.getsize(output_file_path)} bytes")
            with open(output_file_path, 'r') as f:
                logger.debug(f"First 100 characters of extracted_data.json: {f.read(100)}")
        else:
            logger.error(f"extracted_data.json not found at {output_file_path}")

        project.processed_location = output_file_path
        project.save()

        runner_output_dir = os.path.join(output_dir, 'data')
        os.makedirs(runner_output_dir, exist_ok=True)

        runner_command = [
            'python3',
            os.path.join(settings.BASE_DIR, 'retrievals', 'runner.py'),
            '--processed_docs', output_file_path,
            '--method', 'bm25', 'tfidf', 'flash', 'lunr', 'fuzz', 'embedding', 'encoder', 'dpr',
            '--k', '5',
            '--output_dir', runner_output_dir
        ]

        logger.debug(f"Running runner command: {' '.join(runner_command)}")
        try:
            subprocess.run(runner_command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running runner: {e}")
            logger.error(f"Process output: {e.output}")
            logger.error(f"Process error: {e.stderr}")
            return

        project.is_processing_complete = True
        project.save()
        
        logger.info(f"Project {project.name} documents processed. Location: {output_file_path}")

    except Exception as e:
        logger.exception(f"Unexpected error processing documents for project {project_id}: {str(e)}")

        




def run_analysis(project):
    try:
        retrieval_results_path = os.path.join(settings.MEDIA_ROOT, project.name, 'sys', 'temp', 'data', 'retrieval_results.json')
        analysis_output_path = os.path.join(settings.MEDIA_ROOT, project.name, 'sys', 'temp', 'data', 'analysis_output.json')
        project_folder = os.path.join(settings.MEDIA_ROOT, project.name)

        analysis_command = [
            'python',
            'retrievals/analyser.py',
            retrieval_results_path,
            analysis_output_path,
            project_folder
        ]

        logger.debug(f"Running analysis command: {' '.join(analysis_command)}")
        subprocess.run(analysis_command, check=True)

        if os.path.exists(analysis_output_path):
            with open(analysis_output_path, 'r') as f:
                analysis_results = json.load(f)
            return analysis_results
        else:
            logger.error(f"Analysis output file not found: {analysis_output_path}")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running analysis for project {project.name}: {e.stderr}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error running analysis for project {project.name}: {str(e)}")
        return None




@require_GET
def get_project_members(request, project_name):
    try:
        project = Project.objects.get(name=project_name)
        members = project.members.all()
        return JsonResponse({
            'members': [{'username': member.username, 'isOnline': member.is_online, 'isBusy': member.is_busy} for member in members]
        })
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)

@require_GET
def get_online_users(request):
    online_users = User.objects.filter(is_online=True)
    return JsonResponse({
        'users': [{'username': user.username, 'isOnline': user.is_online, 'isBusy': user.is_busy} for user in online_users]
    })
