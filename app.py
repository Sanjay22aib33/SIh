from flask import Flask, render_template, request, redirect, url_for
from langchain.prompts import PromptTemplate
from langchain.llms import CTransformers
from database import get_teachers,get_user_by_email,connect_to_database,get_signup_values
import pytesseract as pyt
import cv2
import os



app = Flask(__name__)


def get_llama_response(input_text, no_words, blog_style):
    llm = CTransformers(model='llama-2-7b-chat.ggmlv3.q2_K.bin',
                        model_type='llama',
                        config={'max_new_tokens': 256, 'temperature': 0.01})
    
    template = """
        Write a blog for {blog_style} job profile for a topic {input_text} within {no_words} words.
    """
    
    prompt = PromptTemplate(input_variables=["blog_style", "input_text", "no_words"], template=template)
    
    response = llm(prompt.format(blog_style=blog_style, input_text=input_text, no_words=no_words))
    return response

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        input_text = request.form['input_text']
        no_words = request.form['no_words']
        blog_style = request.form['blog_style']
        response = get_llama_response(input_text, no_words, blog_style)
        return render_template('result.html', response=response)
    return render_template('index.html')

@app.route('/extract_text', methods=['POST'])
def extract_text():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    if file.filename == r'C:\Users\91999\AppData\Local\Programs\Tesseract-OCR':

        return "No selected file"
    
    if file:
        # Save the uploaded file temporarily
        file_path = "uploaded_file.png"  # Change the file extension if needed
        
        file.save(file_path)
        
        # Read the uploaded image file and extract text
        image = cv2.imread(file_path)
        text = pyt.image_to_string(image)
        
        # Delete the temporary file
        os.remove(file_path)
        
        # Render a template to display the extracted text
        return render_template('text_print.html', text=text)

# Route to render the teacher.html template and display teachers' data
@app.route('/teacher')
def teacher():
    # Fetch teachers' data from the database using get_teachers() function
    teachers = get_teachers()

    if teachers is not None:
        # If data is fetched successfully, render the teacher.html template with the fetched data
        return render_template('teacher.html', teachers=teachers)
    else:
       
        return render_template('error.html', message="Error fetching teachers' data from the database")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get user inputs from the form
        email = request.form['email']
        password = request.form['password']

        # Fetch user data from the database using the email
        user = get_user_by_email(email)

        # Fetch signup values from the database
        signup_values = get_signup_values()

        if signup_values:
            # Check if the email exists in the signup values
            email_exists = False
            for user_data in signup_values:
                if user_data['email'] == email:
                    email_exists = True
                    # Check if the password matches
                    if user_data['password'] == password:
                        # Authentication successful, redirect to dashboard or another page
                        return redirect(url_for('home'))
                    else:
                        # Authentication failed, show an error message
                        error_message = "Invalid email or password. Please try again."
                        return render_template('login.html', error=error_message)

            # If email doesn't exist in the signup values
            if not email_exists:
                error_message = "Email does not exist. Please sign up first."
                return render_template('login.html', error=error_message)

        else:
            # If no signup values fetched, show an error message
            error_message = "Error fetching signup data from the database. Please try again later."
            return render_template('login.html', error=error_message)

    return render_template('login.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        print("Received signup request. Name:", name, "Email:", email)

        # Check if the email already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            error = "Email already exists. Please use a different email."
            print("Error:", error)
            return render_template('signup.html', error=error)

        # Add the new user to the database
        try:
            connection = connect_to_database()
            if connection:
                with connection.cursor() as cursor:
                    query = "INSERT INTO signup (name, email, password) VALUES (%s, %s, %s)"
                    cursor.execute(query, (name, email, password))
                    connection.commit()
                    print("User added to the database successfully.")
        except Exception as e:
            error = "An error occurred. Please try again later."
            print("Error:", e)
            return render_template('signup.html', error=error)
        finally:
            if connection:
                connection.close()

        # Redirect to the login page after successful signup
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Handle the file upload
        if 'file' not in request.files:
            return "No file part"
        # Rest of your file upload handling code
    elif request.method == 'GET':
        # Render the upload page
        return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)

