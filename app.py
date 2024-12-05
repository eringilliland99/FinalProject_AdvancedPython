
#import necessary libraries
from flask import Flask, render_template, url_for, flash, request, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename

###############################################################################################################
# Set up application and instances of database
###############################################################################################################
# set up application
## Create instance of Flash class (WSGI application)
# Add app configurations
UPLOAD_FOLDER_DOCS = 'uploads/docs'
UPLOAD_FOLDER_IMAGES = 'uploads/images'
ALLOWED_EXTENSIONS= {'pdf', 'docx', 'txt'}
ALLOWED_EXTENSIONS_IMAGES = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER_DOCS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_IMAGES, exist_ok=True)

# Helper function to check allowed extensions
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

### Name sets root path for the application, important for locating template and static files.
app = Flask(__name__)
app.config['UPLOAD_FOLDER_DOCS'] = UPLOAD_FOLDER_DOCS
app.config['UPLOAD_FOLDER_IMAGES'] = UPLOAD_FOLDER_IMAGES
app.config['SECRET_KEY'] = os.urandom(24)
# Config = attribute to configure
# 'SQLAlchemy_DATTABASE_URI' = what SQLAlchemy should connect to
# ///test.db: Relative path. If db file does not exist, it is created when the application runs.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///potluck.db'
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['ALLOWED_EXTENSIONS_IMAGES'] = ALLOWED_EXTENSIONS_IMAGES
# instance of SQL alchemy, linked to application.
db = SQLAlchemy(app)

###############################################################################################################
# Initialize class for database input
###############################################################################################################
# Potluck -- class for db that allows user to input their name &  what they're bringing
class Dish(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    contributor = db.Column(db.String(200), nullable = False) # Who is bringing the item
    item_name = db.Column(db.String(200), nullable=False) # What they are bringing
    description = db.Column(db.String(500), nullable=True) # Optional additional details
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return f"<Dish {self.item_name} by {self.contributor}>"

class ChristmasList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChristmasList {self.filename}>"

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Photo {self.filename}>"

# Set up app routes
@app.route('/')
def home():
    return render_template('home_page.html')
################
# Food
################
@app.route('/food_database', methods=['POST', 'GET'])
def food_database():
    if request.method == 'POST':
        # Retrieving data from form
        contributor = request.form['contributor']
        item_name = request.form['item_name']
        description = request.form['description']

        # Create new dish object
        new_dish = Dish(contributor=contributor, item_name=item_name, description=description)

        try:
            db.session.add(new_dish)
            db.session.commit()
            # Redirect to the same page after form submission
            return redirect(url_for('food_database'))
        except:
            return 'There was an issue adding your dish.'

    else:
        # Retrieve all dishes from the database and order by creation date
        dishes = Dish.query.order_by(Dish.date_created).all()
        return render_template('food_database.html', dishes=dishes)


@app.route('/delete/<int:id>')
def delete(id):
    dish_to_delete = Dish.query.get_or_404(id)
    try:
        db.session.delete(dish_to_delete)
        db.session.commit()
        return redirect('/food_database')
    except:
        return 'There was a problem deleting that dish. Call Erin at (xxx)-xxx-xxxx'

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    dish = Dish.query.get_or_404(id)

    if request.method == "POST":
        dish.contributor = request.form['contributor']
        dish.item_name = request.form['item_name']
        dish.description = request.form['description']

        try:
            db.session.commit()
            return redirect('/food_database')  # or use url_for('food_database')
        except:
            return "There was an issue updating your dish. Call Erin at (xxx)-xxx-xxxx"
    else:
        return render_template('update.html', dish=dish)

#############
# Graph!
#############
@app.route('/pie', methods=['GET'])
def pie():
    contributions = db.session.query(Dish.contributor, db.func.count(Dish.id).label('count')).group_by(Dish.contributor).all()
    # Convert to dictionary
    pie_data = {contributor or 'Unknown': count for contributor, count in contributions}
    
    if not pie_data:  # If pie_data is empty
        return render_template('pie.html', data=None)

    return render_template('pie.html', data=pie_data)



#############
# Photos
#############

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMAGES

@app.route('/photo_page', methods=['GET', 'POST'])
def photo_page():
    if request.method == 'POST':
        # Check if the form has a photo and if it's allowed
        if 'photo' not in request.files:
            return redirect(request.url)
        photo = request.files['photo']
        
        if photo and allowed_file(photo.filename):
            # Save the file to the upload folder
            filename = secure_filename(photo.filename)
            filepath = os.path.join(UPLOAD_FOLDER_IMAGES, photo.filename)
            photo.save(filepath)

            # Redirect to the same page to show the uploaded photo
            return redirect(url_for('photo_page'))

    # Fetch all uploaded images from the directory to display in the carousel
    images = os.listdir(UPLOAD_FOLDER_IMAGES)
    
    # Filter out non-image files and return the list of images
    images = [image for image in images if allowed_file(image)]
    
    return render_template('photo_page.html', photos=images)

@app.route('/uploads/docs/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_DOCS'], filename)
@app.route('/uploads/images/<filename>')
def uploaded_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_IMAGES'], filename)
if __name__ == "__main__":
    app.run(debug=True)
