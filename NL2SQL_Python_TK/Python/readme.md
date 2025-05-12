# Natural Language to SQL Query System

This application allows users to query MySQL databases using natural language. It converts user questions into SQL queries using GPT-4o-mini, executes them on a MySQL database, and presents the results with visualizations.

## Features

- **Natural Language Interface**: Ask questions in plain English
- **SQL Generation**: Uses OpenAI's GPT-4o-mini to translate natural language to SQL
- **Database Configuration**: Easy setup for your MySQL connection
- **Query Validation**: Ensures only safe, read-only queries are executed
- **Data Visualization**: Automatic charts based on query results
- **Results Summary**: AI-generated insights about your query results

## Installation

### Installing Python Dependencies

1. First, ensure you have Python 3.7+ installed:
   ```bash
   python --version
   # or
   python3 --version
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

   This will install:
   - mysql-connector-python
   - pandas
   - matplotlib
   - python-dotenv
   - openai

### Installing Tkinter

Tkinter is Python's standard GUI package and is required for this application.

#### Windows
Tkinter is included with standard Python installations on Windows:
1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation, ensure "Install launcher for all users" and "Add Python to PATH" are checked
3. Tkinter will be installed automatically

#### macOS
Tkinter should be included with Python from python.org, but if needed:
1. Using Homebrew:
   ```bash
   brew install python-tk
   ```
2. Alternatively, download Python from [python.org](https://www.python.org/downloads/) which includes Tkinter

#### Ubuntu/Debian Linux
```bash
sudo apt update
sudo apt install python3-tk
```

#### Fedora/RHEL Linux
```bash
sudo dnf install python3-tkinter
```

#### Arch Linux
```bash
sudo pacman -S tk
```

### Verifying Tkinter Installation

To check if Tkinter is installed correctly:
```bash
python -c "import tkinter; tkinter._test()"
```
This should open a small window if Tkinter is installed correctly.

### OpenAI API Key

1. Create a `.env` file in the project directory
2. Add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
3. Alternatively, you can set this in the application's configuration window

### MySQL Requirements

1. Install MySQL Server (5.7+) or MariaDB (10.3+)
   - [MySQL Download](https://dev.mysql.com/downloads/mysql/)
   - [MariaDB Download](https://mariadb.org/download/)

2. Ensure the MySQL server is running:
   ```bash
   # For Linux/Mac
   sudo systemctl status mysql
   
   # For Windows
   net start mysql
   ```

## Database Setup

### Creating the Test Database

1. Log in to your MySQL server:
   ```bash
   mysql -u root -p
   ```

2. Import the sample database script:
   ```bash
   # Method 1: From the MySQL command line
   mysql -u root -p < mysql_setup.sql
   
   # Method 2: From within MySQL client
   source path/to/mysql_setup.sql
   ```

3. Verify the database was created:
   ```sql
   SHOW DATABASES;
   USE nl2sql_test;
   SHOW TABLES;
   ```

The script creates:
- A sample e-commerce database (nl2sql_test)
- Tables for customers, products, categories, orders, and order items
- Sample data with relationships
- A read-only user (nl2sql_user) with password (nlsql_password)
- Analytical views for complex testing

### Creating a MySQL User for the Application

The setup script automatically creates a read-only user, but you can also create it manually. Here's how to create the recommended user with read-only access:

#### Creating the Default NL2SQL User

1. Log in to MySQL as root:
   ```bash
   mysql -u root -p
   ```

2. Create the nl2sql_user with password:
   ```sql
   CREATE USER 'nl2sql_user'@'localhost' IDENTIFIED BY 'nlsql_password';
   ```

3. Grant read-only permissions:
   ```sql
   GRANT SELECT ON nl2sql_test.* TO 'nl2sql_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

4. Verify the user has been created:
   ```sql
   SELECT user, host FROM mysql.user WHERE user = 'nl2sql_user';
   SHOW GRANTS FOR 'nl2sql_user'@'localhost';
   ```

#### Using MySQL Workbench

1. Open MySQL Workbench and connect to your server
2. Navigate to Administration > Users and Privileges
3. Click "Add Account"
4. Enter username "nl2sql_user" and password "nlsql_password"
5. In the "Schema Privileges" tab, select nl2sql_test
6. Check the "SELECT" privilege only
7. Click "Apply"

#### Best Practices for User Security

- Create a user with **read-only** permissions for this application
- Use a strong, unique password (in production environments)
- Avoid using the root user for the application
- Consider restricting the user to connect only from specific hosts
- For production use, create a user with access only to the specific database needed

## Usage

1. Run the application:

```bash
python nl2sql_app.py
```

2. Configure your MySQL database:
   - Go to File > Database Configuration
   - Enter your MySQL host, port, username, password, and database name
   - For the test database, use these credentials:
     - Host: localhost
     - Port: 3306
     - Database: nl2sql_test
     - Username: nl2sql_user
     - Password: nlsql_password
   - Add your OpenAI API key if not already set in the .env file
   - Click "Test Connection" to verify settings
   - Save the configuration

3. Start querying:
   - Type your question in the query box, or select an example
   - Click "Execute Query"
   - View the generated SQL, data results, visualization, and summary

## Testing the Application

### Sample Queries to Try

Once your database is set up, try these natural language queries:

1. "Show me the top 5 customers by total amount spent"
2. "Which product category has the highest sales revenue?"
3. "How many orders were placed in each month?"
4. "What is the average order value by customer?"
5. "Show me sales trends over the past 6 months"
6. "List all products with their quantities sold"
7. "Which customers haven't placed an order in the last 2 months?"
8. "What is the most popular product in the Electronics category?"

### Testing Tips

- Start with simple queries and gradually increase complexity
- Test queries that require joins between tables
- Try questions about time-based trends
- Ask for aggregations (averages, sums, counts)
- Compare the generated SQL with what you would write manually
- Check visualizations for appropriate chart types based on data

## Troubleshooting

- **Connection Issues**: Verify your MySQL server is running and credentials are correct
- **API Key Errors**: Check that your OpenAI API key is valid and has sufficient credits
- **SQL Generation Problems**: Try rephrasing your question if the SQL isn't correct
- **No Data Returned**: Ensure your query makes sense for the database schema
- **Visualization Issues**: Some data structures may not generate ideal charts automatically

## Requirements

- Python 3.7+
- MySQL/MariaDB database
- OpenAI API key (for GPT-4o-mini access)
- Required Python packages (see requirements.txt)

## Security Notes

- The application enforces read-only operations (SELECT queries only)
- All generated SQL is validated before execution
- SQL statements that could modify data (INSERT, UPDATE, DELETE, etc.) are blocked
- Use a read-only MySQL user for additional security

## Architecture

This application implements the NL2SQL architecture described in the system design document:

1. **Natural Language Input**: User enters a question via the UI
2. **NLP Module**: GPT-4o-mini converts the question to SQL
3. **SQL Validation**: Safety checks are performed
4. **API Access Layer**: Connects to the configured MySQL database
5. **SQL Execution**: Runs the query on the database
6. **Data Analysis**: Processes the results
7. **Results Visualization**: Displays data, charts, and summaries
