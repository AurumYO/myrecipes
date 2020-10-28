import os
# pip install pillow
from PIL import Image
from flask import url_for, current_app, render_template
from recblog import mail
from flask_mail import Message
from threading import Thread


def add_profile_pic(pic_upload, username):
    filename = pic_upload.filename
    # Grab extension type .jpg or .png
    ext_type = filename.split('.')[-1]
    storage_filename = str(username) + '.' + ext_type

    filepath = os.path.join(current_app.root_path, 'static/profile_pics', storage_filename)

    # Play Around with this size.
    output_size = (200, 200)

    # Open the picture and save it
    pic = Image.open(pic_upload)
    pic.thumbnail( output_size )
    pic.save(filepath)

    return storage_filename

def send_async_email(current_app, msg):
    with current_app.app_context():
        mail.send(msg)


def send_confirmation_email(to, subject, template, **kwargs):
    msg = Message(current_app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject, sender=current_app.config['FLASKY_MAIL_SENDER'],
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[current_app, msg])
    thr.start()
    return thr


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='nonreply@demo.com', recipients=[user.email])
    msg.body = f"""To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
"""
    mail.send(msg)
