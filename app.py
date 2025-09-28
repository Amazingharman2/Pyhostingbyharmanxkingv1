
import os
import subprocess
import shutil  # For file management operations
import time
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'py'}  # Only allow Python files
app.config['SECRET_KEY'] = '7357297900'  # Change this to a strong, random key!

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ADMIN_PASSWORD = "735729" #Change this default password
LOG_FILE = "app.log"
def log_message(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# Basic admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        password = request.form.get('password')
        if password != ADMIN_PASSWORD:
            flash('Incorrect admin password.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin_login', methods=['GET'])
def admin_login():
    return render_template('admin_login.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_file_status(filename):
    # Implement your logic to determine if the file is running.
    # This is a placeholder.  You'll need to track running processes.
    # A simple approach is to maintain a dictionary mapping filenames to process IDs.
    # Be very careful about race conditions and process management.
    return "Not Running"  # Replace with actual status

def install_pip_package(package_name):
  try:
      subprocess.check_call(['pip', 'install', package_name], timeout=60)
      log_message(f"Successfully installed {package_name}")
      return True, f"Successfully installed {package_name}"
  except subprocess.CalledProcessError as e:
      log_message(f"Error installing {package_name}: {e}")
      return False, f"Error installing {package_name}: {e}"
  except subprocess.TimeoutExpired:
      log_message(f"Timeout installing {package_name}")
      return False, "Timeout installing package."

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle file upload
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename) # Sanitization
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash(f'File "{filename}" uploaded successfully', 'success')
            log_message(f"File {filename} uploaded")
            return redirect(url_for('index'))
        else:
            flash('Invalid file type. Only .py files are allowed.', 'error')
            return redirect(request.url)

    files = os.listdir(app.config['UPLOAD_FOLDER'])
    file_statuses = {filename: get_file_status(filename) for filename in files}
    return render_template('index.html', files=files, file_statuses=file_statuses)


@app.route('/run/<filename>')
def run_script(filename):
    if not allowed_file(filename):
        flash('Invalid file type', 'error')
        return redirect(url_for('index'))

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        flash('File not found', 'error')
        return redirect(url_for('index'))

    try:
        # **SECURITY WARNING:** Running arbitrary code is extremely dangerous.
        # This uses subprocess with a timeout for basic safety, but it's not foolproof.
        # Consider using a more robust sandboxing solution.
        log_message(f"Running {filename}")
        result = subprocess.run(['python', filepath], capture_output=True, text=True, timeout=10, check=False) # added timeout

        if result.returncode == 0:
            output = result.stdout
            flash(f'Script "{filename}" executed successfully.', 'success')
        else:
            output = result.stderr
            flash(f'Script "{filename}" failed with error: {output}', 'error')

        return render_template('script_output.html', filename=filename, output=output)

    except subprocess.TimeoutExpired:
        flash(f'Script "{filename}" timed out.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error running script "{filename}": {e}', 'error')
        log_message(f"Error {filename}: {e}")
        return redirect(url_for('index'))

@app.route('/delete/<filename>')
def delete_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        os.remove(filepath)
        flash(f'File "{filename}" deleted successfully.', 'success')
        log_message(f"File {filename} deleted")
    except OSError as e:
        flash(f'Error deleting file "{filename}": {e}', 'error')
        log_message(f"Error deleting file {filename}: {e}")
    return redirect(url_for('index'))


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/install_package', methods=['POST'])
def install_package():
    package_name = request.form['package_name']
    success, message = install_pip_package(package_name)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('index'))


@app.route('/admin_logs', methods=['GET', 'POST'])
def admin_logs():
    if request.method == 'POST':
      if request.form['action'] == 'get_logs':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
          try:
            with open(LOG_FILE, "r") as f:
              logs = f.read()
            return render_template('admin_logs.html', logs=logs, password_protected=False)
          except FileNotFoundError:
              return render_template('admin_logs.html', logs="Log file not found.", password_protected=False)
        else:
            flash('Incorrect admin password.', 'error')
            return redirect(url_for('admin_logs'))
    return render_template('admin_logs.html', password_protected=True)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# HTML Templates
# Create these files in a 'templates' directory in the same directory as your Python script.
# templates/index.html
# templates/script_output.html
# templates/admin_logs.html
# templates/admin_login.html

# Example index.html
# templates/index.html
