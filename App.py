from flask import Flask, render_template, request,redirect,url_for,session,jsonify,flash
import sqlite3
import secrets
import base64
secret_key=secrets.token_hex(16)
app = Flask(__name__)
app.secret_key = secret_key
#Connection:
app.config['DATABASE'] = 'just_watches.db'
connection_pool = []
def get_db():
    if not connection_pool:
        connection_pool.append(sqlite3.connect(app.config['DATABASE'], check_same_thread=False))
    return connection_pool.pop()

# Closing Coonection:
def close_db(connection):
    connection_pool.append(connection)
    
def close_all_db_connections():
    for connection in connection_pool:
        connection.close()
        
@app.teardown_appcontext
def close_all_connections(exception=None):
    close_all_db_connections()

#Templates of Html:
@app.route('/')
def Home():
    return render_template('Home.html')

@app.route('/App')
def App():
    return render_template('App.html')

@app.route('/About')
def About():
    return render_template('About.html')

@app.route('/App_admin')
def App_admin():
    return render_template('App(Admin).html')

@app.route('/Categories')
def Categories():
    return render_template('categories.html')

@app.route("/Cart")
def Cart():
    return render_template('Cart.html')


@app.route('/Login')
def Login():
    return render_template('Login.html')

@app.route('/Forgot_Password')
def Forgot_Password():
    return render_template('Forgot_Password.html')

@app.route('/Register')
def Register():
    return render_template('Register.html')

@app.route('/Stock')
def Stock():
    return render_template('Stock.html')

@app.route('/Customer')
def Customer():
    return render_template('Customer_detail.html')

# Register:
@app.route('/register', methods=['POST'])
def register():
        user_type = request.form.get('user_type')
        
        # Get form data
        name = request.form['fname']
        cont = request.form['contact']
        email = request.form['email']
        username = request.form['name']
        password = request.form['pass2']
     
        # Generate new customer ID
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT MAX(Customer_ID) FROM Customer')
            result = cursor.fetchone()
            latest_cust_id = result[0] if result[0] is not None else 2021430000
        cust_id = latest_cust_id + 1
        admin_id = 10001
         
        with app.app_context():
         db = get_db()
         cursor = db.cursor()
         cursor.execute('SELECT * FROM Customer WHERE Username = ? AND Email=? AND Phone_No=?', (username,email,cont,))
         existing_user = cursor.fetchone()

        if existing_user:
         error_message = "User Already Exist"
         return redirect(url_for('Register', error_message=error_message))
     
        # Insert new user based on user_type
        if user_type == 'customer':
            with app.app_context():
                db = get_db()
                cursor = db.cursor()
                cursor.execute('INSERT INTO Customer(Customer_ID, Name, Phone_No, Email, Username, Password) VALUES (?, ?, ?, ?, ?, ?)',
                               (cust_id, name, cont, email, username, password))
                db.commit()
            session['user'] = (cust_id, name, cont, email, username, password)
            success_message = "Registration Successful"
            return redirect(url_for('Login', success_message=success_message))

        elif user_type == 'admin':
            with app.app_context():
                db = get_db()
                cursor = db.cursor()
                cursor.execute('INSERT INTO Admin(Admin_Id, Name, Phone_No, Email, Username, Password) VALUES (?, ?, ?, ?, ?, ?)',
                               (admin_id, name, cont, email, username, password))
                db.commit()
            session['user'] = (admin_id, name, cont, email, username, password)
            success_message = "Registration Successful"
            return redirect(url_for('Login', success_message=success_message))

        else:
            return render_template('Login.html')

def recreate_password(pass2,email,cont,user_type):
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()

        if(user_type=='customer'):
            cursor.execute('UPDATE Customer SET Password = ? WHERE Email = ? AND Phone_No = ?', (pass2, email, cont))
        elif(user_type=='admin'):
            cursor.execute('UPDATE Admin SET Password = ? WHERE Email = ? AND Phone_No = ?', (pass2, email, cont))
        else:
            raise ValueError("Invalid user type")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error authenticating password: {e}")
    finally:
        if conn:
            conn.close()

    return False

@app.route('/forget_password', methods=['POST'])
def forget_password():
    email=request.form["email"]
    cont=request.form["contact"]
    user_type=request.form["user_type"]
    session['email'] = email
    session['cont'] = cont
    session['user_type'] = user_type
    
    with app.app_context():
         db = get_db()
         cursor = db.cursor()
         cursor.execute('SELECT * FROM Customer WHERE Email=? AND Phone_No=?', (email,cont,))
         customer = cursor.fetchone()
    
    with app.app_context():
         db = get_db()
         cursor = db.cursor()
         cursor.execute('SELECT * FROM Admin WHERE Email=? AND Phone_No=?', (email,cont,))
         admin = cursor.fetchone()
         
    if customer:
        return render_template('New_Password.html')
    
    elif admin:
        return render_template('New_Password.html')
    
    else:
        error_message='User Not Found'
        return redirect(url_for('Forgot_Password',error_message=error_message))
    
@app.route('/new_password', methods=['POST'])
def new_password():
    pass2=request.form["pass2"]
    email = session.get('email')
    cont = session.get('cont')
    user_type = session.get('user_type')
    if recreate_password(pass2, email, cont, user_type):
        password='Password Updated'
        return redirect(url_for('Login',password=password))
    else:
        return render_template('New_Password.html', error='Error updating password')

# Login:
def authenticate_user(username, password, user_type):
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()

        if user_type == 'customer':
            cursor.execute('SELECT * FROM Customer WHERE Username=? AND Password=?', (username, password))
        elif user_type == 'admin':
            cursor.execute('SELECT * FROM Admin WHERE Username=? AND Password=?', (username, password))
        else:
            raise ValueError("Invalid user type")

        user = cursor.fetchone()

        if user:
            return user
    except Exception as e:
        print(f"Error authenticating user: {e}")
    finally:
        if conn:
            conn.close()

    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['uname']
        password = request.form['upass']
        user_type = request.form.get('user_type')
        remember_me = request.form.get('rm')
        user = authenticate_user(username, password, user_type)
        if user:
            session['user'] = user
            if user_type == 'customer':
                flash('Welcome To Phone Street...', 'error')
                return redirect(url_for('App'))
            elif user_type == 'admin':
                flash('Welcome To Phone Street...', 'error')
                return redirect(url_for('App_admin'))
        else:
           flash('Incorrect Username Or Password', 'error')
           return redirect(url_for('Login'))

   
#Profile:
@app.route('/Profile')
def Profile():
    user= session.get('user')
    if user:
        print("User Data:", user)
        return render_template('Profile.html', user=user)
    else:
        return redirect(url_for('Login'))

#Profil(Admin):
@app.route('/Profile_Admin')
def Profile_Admin():
    user= session.get('user')
    if user:
        print("User Data:", user)
        return render_template('Profile(Admin).html', user=user)
    else:
        return redirect(url_for('Login'))

#Feedback:
@app.route('/feedback', methods=['POST'])
def feedback():
     with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT MAX(Id) FROM Feedback')
        result = cursor.fetchone()
        latest_id = result[0] if result[0] is not None else 0
     Id=latest_id+1  
     name=request.form['name']
     email=request.form['email']
     review=request.form['message']  
     with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO Feedback(Id,Name,Email,Review) VALUES (?, ?, ?, ?)', (Id,name,email,review))
        db.commit()
     success_message = "Thank you..."
     return redirect(url_for('App', success_message=success_message))

#Stock:
@app.route('/stock', methods=['POST'])
def stock():
  if request.method == 'POST':
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT MAX(Stock_ID) FROM Stock')
        result = cursor.fetchone()
        latest_stock_id = result[0] if result[0] is not None else 1430000

    stock_id = latest_stock_id + 1
    product_name = request.form['productName']
    quantity = request.form['quantity']
    price = request.form['price']
    image=request.files['image']
    image_data =  base64.b64encode(image.read()).decode('utf-8')
    with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute('INSERT INTO Stock(Stock_ID,Product_Name,Image,Quantity,Price) VALUES (?,?, ?, ?, ?)',
                           (stock_id, product_name,image_data, quantity, price))
            db.commit()
    add_message = "Stock Add Successfully"
    return redirect(url_for('Stock', add_message=add_message))
  else:
      return render_template('Stock.html')
  
#update_Stock:
@app.route('/update', methods=['POST'])
def update():
  if request.method == 'POST':
    stock_id = request.form['ProductId']
    product_name = request.form['ProductName']
    quantity = request.form['Quantity']
    price = request.form['Price']
    with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute('UPDATE Stock SET Product_Name=?,Quantity=?,Price=? WHERE Stock_Id=?',
                           (product_name, quantity, price,stock_id))
            db.commit()
    update_message = "Stock Update Successfully"
    return redirect(url_for('Stock', update_message=update_message))
  else:
      return render_template('Stock.html')
  
#delete Stock:
@app.route('/delete', methods=['POST'])
def delete():
  if request.method == 'POST':
    stock_id = request.form['ProductId']
    with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute('DELETE FROM Stock WHERE Stock_ID=?',(stock_id,))
            db.commit()
    delete_message = "Stock Delete Successfully"
    return redirect(url_for('Stock', delete_message=delete_message))
  else:
      return render_template('Stock.html')

#Get Stock Data:
@app.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Stock')
        stocks = cursor.fetchall()

    return jsonify(stocks)

#Get Feedback Data:
@app.route('/see_feedback', methods=['GET'])
def see_feedback():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Feedback')
        feedback = cursor.fetchall()

    return jsonify(feedback)

#Get Customer Data:
@app.route('/customer_detail', methods=['GET'])
def customer_detail():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Customer')
        customer = cursor.fetchall()

    return jsonify(customer)

#add_Product:
@app.route('/add_product', methods=['POST'])
def add_product():
    if 'cart' not in session:
        session['cart'] = []
    product_name = request.form['productName']
    quantity = request.form['quantity']
    if is_product_in_stock(product_name, quantity):
        with app.app_context():
          db = get_db()
          cursor = db.cursor()
          cursor.execute('SELECT MAX(Cart_id) FROM Cart')
          result = cursor.fetchone()
          latest_id = result[0] if result[0] is not None else 2021430023
          cart_id=latest_id+1 
          db.commit()
          cursor.execute('SELECT Price FROM Stock WHERE Product_Name = ?', (product_name,))
          price = cursor.fetchone()
          cursor.execute('UPDATE Stock SET Quantity = Quantity - ? WHERE Product_Name = ?', (quantity, product_name))
          db.commit()
          cursor.execute('INSERT INTO Cart(Cart_id,Product_Name,Quantity,Price) VALUES (?,?, ?,?)',
                           (cart_id,product_name,quantity,price[0]))
          db.commit()
          cart=cursor.fetchone()
          session['cart']=cart
          session['cart_id']=cart_id
          print(session['cart'])
        product_add = "Product Add Successfuly"
        return redirect(url_for('Categories', product_add=product_add))
    else:
        not_add = "Oops..Out Of Stock"
        return redirect(url_for('Categories', not_add=not_add))

def is_product_in_stock(product_name, quantity):
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Stock WHERE Product_Name = ? LIMIT 1", (product_name,))
        stock_data = cursor.fetchone()

        if stock_data and stock_data[3] >= int(quantity):
         return True
        else:
         return False
    except Exception as e:
        print(f"Error authenticating user: {e}")
    finally:
        if conn:
            conn.close()
    return False
    
#view_cart:
@app.route('/cart_detail', methods=['GET'])
def cart_detail():
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT * FROM Cart')
            cart = cursor.fetchall()
        cart_data = [{'Cart_id': row[0], 'Product_Name': row[1], 'Quantity': row[2],'Price': row[3]} for row in cart]
        return jsonify(cart_data)

#delete_CART_item:
@app.route('/delete_cart_item', methods=['DELETE'])
def delete_cart_item():
    try:
        data = request.get_json()
        cart_id = data.get('cartId')

        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT Product_Name, Quantity ,Price FROM Cart WHERE Cart_id = ?', (cart_id,))
            cart_item = cursor.fetchone()
            cursor.execute('DELETE FROM Cart WHERE Cart_id = ?', (cart_id,))
            db.commit()
            cursor.execute('UPDATE Stock SET Quantity = Quantity + ? WHERE Product_Name = ?', (cart_item[1], cart_item[0]))
            db.commit()
            cursor.close()
            return jsonify({'message': 'Cart item deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# delete_all_cart_items:
@app.route('/delete_all_cart_items', methods=['DELETE'])
def delete_all_cart_items():
    try:
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute('DELETE FROM Cart')
            db.commit()
            cursor.close()
            return jsonify({'message': 'All cart items deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#app_to_cart:
@app.route('/app_to_cart', methods=['POST'])
def app_to_cart():
    try:
        product_name = request.form.get('product_name')
        quantity = request.form.get('quantity')

        if is_product_in_stock(product_name, quantity):
            with app.app_context():
                db = get_db()
                cursor = db.cursor()
                cursor.execute('SELECT MAX(Cart_id) FROM Cart')
                result = cursor.fetchone()
                latest_id = result[0] if result[0] is not None else 2021430023
                cart_id = latest_id + 1

                cursor.execute('SELECT Price FROM Stock WHERE Product_Name = ?', (product_name,))
                price = cursor.fetchone()

                cursor.execute('UPDATE Stock SET Quantity = Quantity - ? WHERE Product_Name = ?', (quantity, product_name))
                db.commit()

                cursor.execute('INSERT INTO Cart(Cart_id, Product_Name, Quantity, Price) VALUES (?, ?, ?, ?)',
                               (cart_id, product_name, quantity, price[0]))
                db.commit()

                # Assuming you want to store cart details in the session
                session['cart'] = {'cart_id': cart_id, 'product_name': product_name, 'quantity': quantity, 'price': price[0]}

            return jsonify({'message': 'Product added to cart successfully'})
        else:
            return jsonify({'error': 'Product is not in stock or quantity is insufficient'})
    except Exception as e:
        # Handle any exceptions
        return jsonify({'error': str(e)})

# Logout:
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('Home'))

if __name__ == '__main__':
    app.run(debug=True)