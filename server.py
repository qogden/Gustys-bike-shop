import os
import psycopg2
import psycopg2.extras

from flask.ext.socketio import SocketIO, emit
from flask import Flask, render_template, request, session, redirect, render_template_string

from sqlalchemy import create_engine, MetaData
from flask.ext.login import UserMixin, LoginManager, login_user, logout_user
from flask.ext.blogging import SQLAStorage, BloggingEngine

app = Flask(__name__)

app.secret_key = os.urandom(24).encode('hex')
app.config['SECRET_KEY'] = 'secret!'
app.config["BLOGGING_URL_PREFIX"] = "/blog"
app.config["BLOGGING_DISQUS_SITENAME"] = "test"
app.config["BLOGGING_SITEURL"] = "http://localhost:8000"
socketio = SocketIO(app)

# blogging extensions
engine = create_engine('sqlite:////tmp/blog.db')
meta = MetaData()
sql_storage = SQLAStorage(engine, metadata=meta)
blog_engine = BloggingEngine(app, sql_storage)
login_manager = LoginManager(app)
meta.create_all(bind=engine)

# blog authentication
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

    def get_name(self):
        return "Gusty Cooper"  
        
@login_manager.user_loader
@blog_engine.user_loader
def load_user(user_id):
    return User(user_id)

def connectToDB():
  connectionString = 'dbname=bikes user=biker password=bike123 host=localhost'
  print connectionString
  try:
    return psycopg2.connect(connectionString)
  except:
    print("Can't connect to database")

@socketio.on('connect')
def makeConnection():
	totals = getTotals()
	emit('totals', totals)
	print('connected')

@app.route('/')
def index():
	if("email" not in session):
		session['email']=''
	 	session['loggedin'] = False
		session['employee'] = False
	 	session['manager'] = False
	 	session['sales'] = False
	 	session['master'] = False
	
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	cur.execute("SELECT * FROM products")
	stock = cur.fetchall()
	conn.commit()
	
	i=0
	products = []
	for row in stock:
		for row in stock[i]:
			p = stock[i]
			items = {'id':p[0], 'name':p[1], 'image':p[2], 'price':p[4]}
		products.append(items)
		i+=1
	
	cur.execute("SELECT * FROM products WHERE producttype = (SELECT id FROM producttype WHERE producttype = 'bicycles')")
	stock = cur.fetchall()
	conn.commit()
	
	i=0
	feature = []
	for row in stock:
		for row in stock[i]:
			p = stock[i]
			items = {'id':p[0], 'name':p[1], 'image':p[2]}
		feature.append(items)
		i+=1
	return render_template('index.html', stock = products)

@app.route('/logout')
def logout():
	session['email'] = ''
	session['loggedin'] = False
	session['employee'] = False
	session['manager'] = False
	session['sales'] = False
	session['master'] = False
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	cur.execute("SELECT * FROM products")
	stock = cur.fetchall()
	#print stock
	conn.commit()
	
	i=0
	products = []
	for row in stock:
		for row in stock[i]:
			p = stock[i]
			items = {'id':p[0], 'name':p[1], 'image':p[2], 'price':p[4]}
		products.append(items)
		i+=1
	#print products
	
	cur.execute("SELECT * FROM products WHERE producttype = (SELECT id FROM producttype WHERE producttype = 'bicycles')")
	stock = cur.fetchall()
	#print stock
	conn.commit()
	
	i=0
	feature = []
	for row in stock:
		for row in stock[i]:
			p = stock[i]
			items = {'id':p[0], 'name':p[1], 'image':p[2]}
		feature.append(items)
		i+=1
	#print products
	logout_user()
	return render_template('index.html', stock = products)


@app.route('/login')
def login():
	print(session['email'])
	#user = User("testuser")
	#login_user(user)
	return render_template('login.html')
	

@app.route('/login', methods=['POST'])
def access():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	
	query = cur.mogrify("SELECT * FROM users WHERE email = %s", (request.form['email'], ))
	cur.execute(query)
	cur.fetchall()
	emailresults = cur.rowcount
	conn.commit()
	
	noEmail = False
	wrongPassword = False
	print(session['email'])
	
	if(emailresults == 1):
		query = cur.mogrify("SELECT * FROM users WHERE email = %s AND password = crypt(%s, password)", (request.form['email'], request.form['password']))
		cur.execute(query)
		cur.fetchall()
		passwordresults = cur.rowcount
		conn.commit()
		loggedin = True
		
		if(passwordresults == 1):
			query = cur.mogrify("SELECT * FROM employees WHERE email = %s", (request.form['email'], ))
			cur.execute(query)
			cur.fetchall()
			employeeresults = cur.rowcount
			conn.commit()
			
			if(employeeresults == 1):
				session['email'] = request.form['email']
				session['loggedin'] = True
				session['employee'] = True

				cur.execute("SELECT * FROM employees WHERE email = %s and employeetype = 1", (request.form['email'], ))
				cur.fetchall()
				query = cur.rowcount
				conn.commit()
				
				if(query == 1):
					print("master")
					session['master'] = True
					user = User("testuser")
					login_user(user)
				elif(query != 1):
					print("trying manager")
					cur.execute("SELECT * FROM employees WHERE email = %s and employeetype = 2",(request.form['email'], ))
					cur.fetchall()
					q = cur.rowcount
					conn.commit()
					
					if(q == 1):
						print("manager")
						session['manager'] = True
					
					if(q != 1):
						print("trying sales")
						cur.execute("SELECT * FROM employees WHERE email = %s and employeetype = 3",(request.form['email'], ))
						cur.fetchall()
						conn.commit()
						if(cur.rowcount == 1):
							print("sales")
							session['sales'] = True
						

				return render_template('index.html')
				#return redirect('/timesheet')
			else:
				session['email'] = request.form['email']
				session['loggedin'] = True
				session['employee'] = False
				#switch all unregistered user products onto the customer
				
				cur.execute("SELECT * FROM products")
				stock = cur.fetchall()
				print stock
				conn.commit()
				
				i=0
				products = []
				for row in stock:
					for row in stock[i]:
						p = stock[i]
						items = {'id':p[0], 'name':p[1], 'image':p[2], 'price':p[4]}
					products.append(items)
					i+=1
				print products
				
				cur.execute("SELECT * FROM products WHERE producttype = (SELECT id FROM producttype WHERE producttype = 'bicycles')")
				stock = cur.fetchall()
				print stock
				conn.commit()
				
				i=0
				feature = []
				for row in stock:
					for row in stock[i]:
						p = stock[i]
						items = {'id':p[0], 'name':p[1], 'image':p[2]}
					feature.append(items)
					i+=1
				print products
				return render_template('index.html', stock = products)
				
		else:
			wrongPassword = True
			return render_template('login.html', wrongPassword = wrongPassword)
	else:
		noEmail = True
		return render_template('login.html', noEmail = noEmail)

@app.route('/signup')
def signup2():
	print(session['email'])
	return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	
	print(request.form['firstname'], request.form['lastname'], request.form['email'], request.form['password'], request.form['confirmpassword'])
	
	noPassMatch = False
	emailTaken = False
	
	query = cur.mogrify("SELECT * FROM users WHERE email = %s", (request.form['email'], ))
	cur.execute(query)
	cur.fetchall()
	emailresults = cur.rowcount
	conn.commit()
	
	print(session['email'])
	
	if(emailresults != 0):
		emailTaken = True
		message1='Email taken'
		print(message1)
		return render_template('account.html', emailTaken = emailTaken)
	
	if(request.form['password'] != request.form['confirmpassword']):
		noPassMatch = True
		message1='Passwords do not match'
		print(message1)
		return render_template('account.html', noPassMatch = noPassMatch)
		
	try:
		session['email'] = request.form['email']
		session['loggedin'] = True
		cur.execute("INSERT INTO users(email, password) VALUES(%s, crypt(%s, gen_salt('bf')))", (request.form['email'], request.form['password']))
		conn.commit()
		cur.execute("INSERT INTO customers(firstname, lastname, email) VALUES(%s, %s, (SELECT email FROM users WHERE email = %s))", (request.form['firstname'], request.form['lastname'], request.form['email']))
		conn.commit()
		return render_template('signup2.html')
	except:
		print("ERROR inserting into customer")
		print("INSERT INTO users(email, password) VALUES(%s, crypt(%s, gen_salt('bf')))" % (request.form['email'], request.form['password']) )
		print("TRIED: INSERT INTO customers(firstname, lastname, email) VALUES(%s, %s, (SELECT email FROM users WHERE email = %s))" % (request.form['firstname'], request.form['lastname'], request.form['email']))
		conn.rollback()
		return render_template('signup.html')
	conn.commit()
	
@app.route('/single', methods=['POST'])
def single():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	
	pid = request.form['pidi']

	cur.execute("SELECT * FROM products WHERE id = %s", (pid, ))
	p = cur.fetchone()
	conn.commit()
	
	item = {'id':p[0], 'name':p[1], 'image':p[2], 'description':p[3], 'price':p[4], 'stock':p[5]}
	print(item)
	
	cur.execute("SELECT * FROM reviews WHERE productid = %s", (p[0],))
	r = cur.fetchall()
	conn.commit()
	
	reviews = []
	i=0
	for row in r:
		cur.execute("SELECT firstname FROM customers WHERE id = %s", (r[i][1],))
		c = cur.fetchone()
		conn.commit()
		comment = {'customer':c[0], 'day':r[i][3], 'rating':r[i][4], 'comment':r[i][5]}
		reviews.append(comment)
		i+=1
	
	return render_template('single.html', item = item, reviews = reviews)
	

@app.route('/review', methods=['POST'])	
def review():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	
	productid = request.form['productid']
	rating = request.form['rating']
	comment = request.form['comment']
	
	cur.execute("INSERT INTO reviews(customerid, productid, day, rating, comment) VALUES((SELECT id FROM customers WHERE email = %s), %s, (SELECT CURRENT_DATE), %s, %s)", (session['email'], productid, rating, comment))
	conn.commit()
	
	return render_template('reviewcreated.html')
	
	
@app.route('/bikes')
def products():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	cur.execute("SELECT * FROM products WHERE producttype = (SELECT id FROM producttype WHERE producttype = 'bicycles')")
	stock = cur.fetchall()
	print stock
	conn.commit()
	
	i=0
	products = []
	for row in stock:
		for row in stock[i]:
			p = stock[i]
			items = {'id':p[0], 'name':p[1], 'image':p[2], 'price':p[4]}
		products.append(items)
		i+=1
	print products
	
	return render_template('bikes.html', stock = products)
	
@app.route('/parts')
def parts():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	cur.execute("SELECT * FROM products WHERE producttype = (SELECT id FROM producttype WHERE producttype = 'parts')")
	stock = cur.fetchall()
	print stock
	conn.commit()
	
	i=0
	products = []
	for row in stock:
		for row in stock[i]:
			p = stock[i]
			items = {'id':p[0], 'name':p[1], 'image':p[2], 'price':p[4]}
		products.append(items)
		i+=1
	print products
	return render_template('parts.html', stock = products)
	
@app.route('/tools')
def tools():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	cur.execute("SELECT * FROM products WHERE producttype = (SELECT id FROM producttype WHERE producttype = 'tools')")
	stock = cur.fetchall()
	print stock
	conn.commit()
	
	i=0
	products = []
	for row in stock:
		for row in stock[i]:
			p = stock[i]
			items = {'id':p[0], 'name':p[1], 'image':p[2], 'price':p[4]}
		products.append(items)
		i+=1
	print products
	return render_template('tools.html', stock = products)

@app.route('/account', methods=['GET','POST'])
def update_account_info():
	# Placeholder Data
	info = {'fname':'John', 'lname':'Smith',
			'bstreet':'rocky road','bstreet2':'','bcity':'the ricksburg','bstate':'solid','bzip':'1234',
			'sstreet':'rocky road','sstreet2':'','scity':'the ricksburg','sstate':'solid','szip':'1234',
			'cardno':'1234567','csc':'666','exp':'now'}
	
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	
	print ("STARTTHING")
	if request.method == 'POST':
		if request.form["updatebutton"] == 'UpdateUser':
			cur.execute("UPDATE customers SET firstname = %s, lastname = %s WHERE email = %s", (request.form['firstname'],request.form['lastname'],session['email']))
			conn.commit()
			
		if request.form["updatebutton"] == 'UpdateBilling':
			cur.execute("UPDATE customers SET bstreet1 = %s, bstreet2 = %s, bcity = %s, bstate = %s, bzip = %s WHERE email = %s", (request.form['bstreet'],request.form['bstreet2'],request.form['bcity'],request.form['bstate'],request.form['bzip'],session['email']))
			conn.commit()

		if request.form["updatebutton"] == 'UpdateShipping':
			cur.execute("UPDATE customers SET sstreet1 = %s, sstreet2 = %s, scity = %s, sstate = %s, szip = %s WHERE email = %s", (request.form['sstreet'],request.form['sstreet2'],request.form['scity'],request.form['sstate'],request.form['szip'],session['email']))
			conn.commit()
			
		if request.form["updatebutton"] == 'UpdateCredit':
			cur.execute("UPDATE customers SET cardno = %s, csc = %s, exp = %s WHERE email = %s", (request.form['cardno'],request.form['csc'], request.form['exp'],session['email']))
			conn.commit()

		
	cur.execute("SELECT firstname FROM customers WHERE email = %s", (session['email'],))
	info["fname"] = cur.fetchall()[0][0]
	cur.execute("SELECT lastname FROM customers WHERE email = %s", (session['email'],))
	info["lname"] = cur.fetchall()[0][0]
	
	cur.execute("SELECT bstreet1 FROM customers WHERE email = %s", (session['email'],))
	info["bstreet"] = cur.fetchall()[0][0]
	cur.execute("SELECT bstreet2 FROM customers WHERE email = %s", (session['email'],))
	info["bstreet2"] = cur.fetchall()[0][0]
	cur.execute("SELECT bcity FROM customers WHERE email = %s", (session['email'],))
	info["bcity"] = cur.fetchall()[0][0]
	cur.execute("SELECT bstate FROM customers WHERE email = %s", (session['email'],))
	info["bstate"] = cur.fetchall()[0][0]
	cur.execute("SELECT bzip FROM customers WHERE email = %s", (session['email'],))
	info["bzip"] = cur.fetchall()[0][0]
	
	cur.execute("SELECT sstreet1 FROM customers WHERE email = %s", (session['email'],))
	info["sstreet"] = cur.fetchall()[0][0]
	cur.execute("SELECT sstreet2 FROM customers WHERE email = %s", (session['email'],))
	info["sstreet2"] = cur.fetchall()[0][0]
	cur.execute("SELECT scity FROM customers WHERE email = %s", (session['email'],))
	info["scity"] = cur.fetchall()[0][0]
	cur.execute("SELECT sstate FROM customers WHERE email = %s", (session['email'],))
	info["sstate"] = cur.fetchall()[0][0]
	cur.execute("SELECT szip FROM customers WHERE email = %s", (session['email'],))
	info["szip"] = cur.fetchall()[0][0]
	
	cur.execute("SELECT cardno FROM customers WHERE email = %s", (session['email'],))
	info["cardno"] = cur.fetchall()[0][0]
	cur.execute("SELECT csc FROM customers WHERE email = %s", (session['email'],))
	info["csc"] = cur.fetchall()[0][0]
	cur.execute("SELECT exp FROM customers WHERE email = %s", (session['email'],))
	info["exp"] = cur.fetchall()[0][0]
	return render_template('account.html', info=info)

@app.route('/timesheet', methods=['GET','POST'])
def display_timesheets():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	
	if request.method == 'POST':
		cur.execute("SELECT id FROM employees WHERE email = %s", (session['email'],))
		conn.commit()
		cur.execute("SELECT t_date FROM timesheet WHERE employeeid = %s AND t_date = (SELECT CURRENT_DATE)", (cur.fetchall()[0][0],))
		conn.commit() #clear curser
		numrows = cur.rowcount
		cur.fetchall() 
		if(numrows > 0):
			cur.execute("SELECT id FROM employees WHERE email = %s", (session['email'],))
			conn.commit()
			cur.execute("UPDATE timesheet SET hours = %s WHERE employeeid = %s and t_date = (SELECT CURRENT_DATE)", (request.form['hours'],cur.fetchall()[0][0]))
			conn.commit()
		else:
			cur.execute("INSERT INTO timesheet(employeeid, t_date, hours) VALUES((SELECT id FROM employees WHERE email = %s), (SELECT CURRENT_DATE), %s)", (session['email'], request.form['hours']))
			conn.commit()
		

	#Display current timesheet data(after update)
	timesheet = []
	cur.execute("SELECT id FROM employees WHERE email = %s", (session['email'],))
	conn.commit()
	cur.execute("SELECT t_date, hours FROM timesheet WHERE employeeid = %s ORDER BY t_date desc", (cur.fetchall()[0][0],))
	data = cur.fetchall()
	conn.commit()

	timesheet=[]
	i=0
	for index in data:
		time = data[i][0].date()
		print('time', time, data[i][1])
		
		entry = {'date':time, 'hours':data[i][1]}
		timesheet.append(entry)
		i+=1
	
	return render_template('timesheet.html', timesheet=timesheet)

@app.route('/addAccount')
def addAccount():
	return render_template('addAccount.html')
	
@app.route('/addProduct')
def addProduct():
	return render_template('addProduct.html')
	
@app.route('/contact')
def contact():
	return render_template('contact.html')
	
@socketio.on('addToCart')	
def addToCart(productid, quantity):
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	print(productid, quantity)
	print(session['email'])
	
	cur.execute("SELECT id FROM customers WHERE email = %s", (session['email'], ))
	customerid = cur.fetchone()
	customerid=customerid[0]
	conn.commit()
	
	cur.execute("SELECT * FROM cart WHERE customerid = %s and productid = '%s'", (customerid, productid))
	query=cur.fetchall()
	conn.commit()
	
	if(cur.rowcount == 0):
		cur.execute("INSERT INTO cart(customerid, day, productid, quantity) VALUES(%s, (SELECT CURRENT_DATE), %s, '%s')", (customerid, productid, quantity))
		conn.commit()
	else:
		cur.execute("SELECT quantity FROM cart WHERE customerid = %s and productid = '%s'", (customerid, productid))
		qty = cur.fetchone()
		conn.commit()
		
		quantity = qty[0] + quantity
		
		cur.execute("UPDATE cart SET quantity = %s WHERE customerid = %s and productid = '%s'", (quantity, customerid, productid))
		conn.commit()
	
	message='item has been added'
	totals = getTotals()
	print(message,": ",totals)

	emit('totals',totals)

@socketio.on('cart')
def cart():
	totals = getTotals()
	emit('totals', totals)

@app.route('/cart')
def cart1():
	products = getProducts()
	totals = getTotals()
	return render_template('cart.html', cart = products, totals = totals)
	
@socketio.on('cartqty')
def cartqty(productid, quantity):
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	print('cartqty')
	print(productid)
	print(quantity)
	
	cur.execute("SELECT id FROM customers WHERE email = %s", (session['email'], ))
	customerid = cur.fetchall()
	conn.commit()
	
	customerid = customerid[0][0]
	print(customerid)
	cur.execute("UPDATE cart SET quantity = %s WHERE customerid = %s AND productid = '%s'", (quantity, customerid, productid))
	print('adjusted')
	conn.commit()
	
	totals=getTotals()
	emit('totals', totals)

@app.route('/cartrm', methods=['post'])
def cartrm():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	cur.execute("SELECT id FROM customers WHERE email = %s", (session['email'], ))
	customerid = cur.fetchall()
	conn.commit()
		
	customerid = customerid[0][0]
	productid = request.form['cartrm']
	
	cur.execute("DELETE FROM cart WHERE customerid = %s AND productid = %s", (customerid, productid))
	conn.commit()
	return redirect('/cart')

@app.route('/ordersummary')
def ordersummary():
	
	userinfo = getUserInfo()
	products = getProducts()
	totals = getTotals()
	
	return render_template('ordersummary.html', info = userinfo, cart = products, totals = totals)

def getUserInfo():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	
	cur.execute("SELECT * FROM customers WHERE email = %s", (session['email'], ))
	r = cur.fetchall()
	conn.commit()
	
	i = 0
	j = 0
	for row in r:
		for now in r[i]:
			if r[i][j] == None:
				r[i][j] = ''
			print r[i][j]
			j+=1
		i+=1

	cur.execute("SELECT cardno, csc FROM customers WHERE email = %s", (session['email'], ))
	r2 = cur.fetchall()
	conn.commit()

	

	userInfo = {'first': r[0][1], 'last':r[0][2], 'email':r[0][3], 'bstreet': r[0][4], 'bstreet2': r[0][5], 'bcity':r[0][6], 'bstate':r[0][7], 'bzip':r[0][8], 'sstreet': r[0][9], 'sstreet2': r[0][10], 'scity':r[0][11], 'sstate':r[0][12], 'szip':r[0][13], 'cardno':r[0][14], 'csc':r[0][15], 'exp':r[0][16]}
		
	return userInfo

def getProducts():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	
	cur.execute("SELECT id FROM customers WHERE email = %s", (session['email'], ))
	customerid = cur.fetchall()

	customerid = customerid[0][0]
	conn.commit()

	cur.execute("SELECT * FROM cart WHERE customerid = %s ORDER BY productid", (customerid, ))
	cart = cur.fetchall()
	
	conn.commit()
	
	i=0
	j=0
	k=0
	products = []
	for row in cart:
		c=cart[i]
		cur.execute("SELECT * FROM products WHERE id = %s", (c[3], ))
		item = cur.fetchall()
		conn.commit()
		for row in item:
			p=item[j]	
			items = [p[0], p[1], p[2], p[4], c[4]]
		products.append(items)
		i+=1
	#print products
	return products

def getTotals():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	if (session['loggedin'] and session['employee'] == False):
		query = cur.mogrify("SELECT id FROM customers WHERE email = %s", (session['email'], ))
		cur.execute(query)
		customerid = cur.fetchall()
		customerid = customerid[0][0]
		conn.commit()
		
		cur.execute("SELECT * FROM cart WHERE customerid = %s", (customerid, ))
		cart = cur.fetchall()
		conn.commit()
		
		subtotal = 0.00
		tax = 0.00
		shipping = 0.00
		total = 0.00
		
		i=0
		j=0
		k=0
		count = 0
		for row in cart:
			c=cart[i]
			cur.execute("SELECT * FROM products WHERE id = %s", (c[3], ))
			item = cur.fetchall()
			conn.commit()
			for row in item:
				p=item[j]	
				count = count + c[4]
				subtotal = subtotal + (float(p[4])*float(c[4]))
			i+=1
	else:
		subtotal = 0.00
		tax = 0.00
		shipping = 0.00
		total = 0.00
		count = 0

	if (subtotal != 0.00):
		shipping = 50.00
	tax = subtotal * 0.15
	tax = round(tax,2)
	total = subtotal+ tax + shipping
	
	subtotal = "{0:.2f}".format(subtotal)
	tax = "{0:.2f}".format(tax)
	shipping = "{0:.2f}".format(shipping)
	total = "{0:.2f}".format(total)
	
	totals={'total':total, 'subtotal':subtotal, 'tax':tax, 'shipping':shipping, 'count': count}
	
	return totals

@app.route('/orderconfirmation', methods=['POST'])
def order():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	
	firstname = request.form['firstname']
	lastname = request.form['lastname']
	email = request.form['email']
	
	bstreet = request.form['bstreet']
	bstreet2 = request.form['bstreet2']
	bcity = request.form['bcity']
	bstate = request.form['bstate']
	bzip = request.form['bzip']
	
	sstreet = request.form['sstreet']
	sstreet2 = request.form['sstreet2']
	scity = request.form['scity']
	sstate = request.form['sstate']
	szip = request.form['szip']
	
	cardno = request.form['cardno']
	csc = request.form['csc']
	exp = request.form['exp']
	#print(exp)
	
	status="processing"
	cur.execute("INSERT INTO orders(customerid, orderdate, status, firstname, lastname, email, bstreet, bstreet2, bcity, bstate, bzip, sstreet, sstreet2, scity, sstate, szip, cardno, csc, exp) VALUES ((SELECT id FROM customers WHERE email = %s), (SELECT current_timestamp), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (session['email'], status, firstname, lastname, email, bstreet, bstreet2, bcity, bstate, bzip, sstreet, sstreet2, scity, sstate, szip, cardno, csc, exp))
	conn.commit()
	
	cur.execute("SELECT currval('orders_id_seq')")
	orderid = cur.fetchone()
	conn.commit()
	orderid=orderid[0]
	#print("orderid:", orderid)

	product = getProducts()
	#print(products)
	i=0
	for row in product:
		productid = product[i][0]
		price = product[i][3]
		qty = product[i][4]
		cur.execute("INSERT INTO orderitems(orderid, productid, price, quantity) VALUES(%s, %s, %s, %s)", (orderid, productid, price, qty))
		conn.commit()
		i+=1
	cur.execute("DELETE FROM cart WHERE customerid = (SELECT id FROM customers WHERE email = %s)", (session['email'],))
	conn.commit()
	return render_template('orderconfirmation.html', orderid = orderid)

@app.route('/orders')
def orders():
	conn = connectToDB()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	
	cur.execute("SELECT distinct orderid, productid, price, quantity, status FROM orderitems INNER JOIN orders ON id = orderid WHERE customerid = (SELECT id FROM customers WHERE email = %s) ORDER BY orderid desc", (session['email'],))
	history=cur.fetchall()
	count = cur.rowcount
	conn.commit()
	
	allorders=[]
	order=[]
	i=0
	while (count != 0):
		
		orderid = history[i][0]
		
		while (count != 0 and orderid == history[i][0]):
			print('i',i,'row', history[i][0])
			cur.execute("SELECT name, image FROM products WHERE id = %s", (history[i][1],))
			p = cur.fetchone()
			conn.commit()
			
			cur.execute("SELECT orderdate FROM orders WHERE id = %s", (history[i][0],))
			orderdate = cur.fetchone()
			conn.commit()

			cur.execute("SELECT EXTRACT(month from timestamp %s)", (orderdate[0],))
			month = cur.fetchone()
			conn.commit()

			cur.execute("SELECT EXTRACT(day from timestamp %s)", (orderdate[0],))
			day = cur.fetchone()
			conn.commit()
			
			cur.execute("SELECT EXTRACT(year from timestamp %s)", (orderdate[0],))
			year = cur.fetchone()
			conn.commit()
			
			orderdate = "{0:.0f}".format(month[0])+'-'+"{0:.0f}".format(day[0])+'-'+"{0:.0f}".format(year[0])
			
			orderitems = {'orderid':history[i][0], 'orderdate':orderdate, 'productid':history[i][2], 'name':p[0], 'image':p[1], 'price':history[i][2], 'quantity':history[i][3], 'status':history[i][4]}
			#print('orderitem',orderitems)
			order.append(orderitems)
			#print('order',order)
			i+=1
			count-=1

		allorders.append(order)
		order=[]
		
		#print('allorders',allorders)
	return render_template('order.html', order=allorders)


# start the server
if __name__ == '__main__':
    socketio.run(app,host=os.getenv('IP', '0.0.0.0'), port =int(os.getenv('PORT', 8080)), debug=True)