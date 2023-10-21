from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)

# In-memory data structures
groups = {}
users = {}
images = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        group_name = request.form['group_name']
        user_name = request.form['user_name']
        uploaded_file = request.files['file']

    # Image size restriction
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

    if (request.content_length or 0) > MAX_IMAGE_SIZE:
        flash('アップロードされた画像が大きすぎます。5MB以下の画像をアップロードしてください。', 'error')
        return redirect(url_for('index'))

    # Image format restriction
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    if not allowed_file(uploaded_file.filename):
        flash('許可されていない画像形式です。PNG, JPG, JPEG, GIF のみアップロード可能です。', 'error')
        return redirect(url_for('index'))

    # Verify the image format further
    try:
        image = Image.open(uploaded_file)
        image.verify()  # This will check the consistency of the image
    except:
        flash('無効な画像ファイルです。', 'error')
        return redirect(url_for('index'))


        # Check if group already exists
        if group_name in groups:
            # Joining an existing group
            user_type = "participant"
        else:
            # Creating a new group
            groups[group_name] = {
                'users': [],
                'images': [],
                'random_image': None
            }
            user_type = "creator"

        # Save user details
        users[user_name] = {
            'group_name': group_name,
            'user_type': user_type,
            'image': uploaded_file.filename
        }

        # Save the uploaded image
        img_path = os.path.join("./static/uploads/", uploaded_file.filename)
        uploaded_file.save(img_path)
        images[uploaded_file.filename] = img_path

        groups[group_name]['users'].append(user_name)
        groups[group_name]['images'].append(uploaded_file.filename)  # Saving filename instead of path

        if user_type == "creator":
            groups[group_name]['random_image'] = uploaded_file.filename

        session['user_name'] = user_name
        flash('Image uploaded successfully!', 'success')
        return redirect(url_for('waiting'))

    return render_template('upload.html')

@app.route('/waiting', methods=['GET'])
def waiting():
    user_name = session.get('user_name')
    group_name = users[user_name]['group_name']
    current_group = groups[group_name]
    if len(current_group['users']) == 2:  # Adjust this number if needed
        return redirect(url_for('voting'))
    return render_template('waiting.html')

@app.route('/check_game_start', methods=['GET'])
def check_game_start():
    user_name = session.get('user_name')
    group_name = users[user_name]['group_name']
    current_group = groups[group_name]
    if len(current_group['users']) == 2:  # Adjust this number if needed
        return "started"
    return "waiting"

@app.route('/voting', methods=['GET', 'POST'])
def voting():
    user_name = session.get('user_name')
    group_name = users[user_name]['group_name']
    current_group = groups[group_name]
    result_image = None
    wrong_guessed_image = None
    all_images = []
    message = None

    random_image = images[current_group['random_image']]

    if request.method == 'POST':
        selected_user = request.form.get('vote')
        creator_name = [user for user, details in users.items() if details['user_type'] == 'creator' and details['group_name'] == group_name][0]
        if selected_user == creator_name:
            message = f"Correct! The image was uploaded by {creator_name}."
            all_images = [images[img] for img in current_group['images']]
        else:
            message = "Incorrect!"
            wrong_guessed_image = images[users[selected_user]['image']]

    return render_template('vote.html', image_file=random_image, users=current_group['users'], result_image=result_image, message=message, all_images=all_images, wrong_guessed_image=wrong_guessed_image)

if __name__ == '__main__':
    app.run(debug=True)
