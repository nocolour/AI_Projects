# NL2SQL - Natural Language to SQL Query System

## Overview
NL2SQL is a web-based application that converts natural language questions into SQL queries. It leverages OpenAI's language models to interpret user questions and generate appropriate SQL statements to query databases.

## Features
- Convert natural language questions to SQL queries
- Execute queries on connected MySQL databases
- View results in table, chart, and summary formats
- Configure database connections and API settings
- Example queries for quick testing
- Database schema viewer

## Requirements
- PHP 7.4 or higher
- MySQL database
- OpenAI API key
- Web server (Apache, Nginx, etc.)

## Installation
1. Clone this repository to your web server
2. Ensure the web server has PHP with MySQL support enabled
3. Open the application in a web browser
4. Configure your database connection in Settings
5. Add your OpenAI API key in Settings

## XAMPP Setup
To host this application using XAMPP:

1. Install XAMPP from [https://www.apachefriends.org/](https://www.apachefriends.org/)
2. Clone or download this repository to your XAMPP's htdocs folder (e.g., `C:\xampp\htdocs\NL2SQL` on Windows or `/Applications/XAMPP/htdocs/NL2SQL` on macOS)
3. Start the Apache and MySQL services from the XAMPP Control Panel
4. Access the application by navigating to `http://localhost/NL2SQL/Test_experiment/Python/PHP_Frontend/` in your web browser
5. If you encounter permission issues, ensure the Apache user has read/write access to the application directory
6. For database connectivity, create your database in phpMyAdmin (accessible at `http://localhost/phpmyadmin`) and update the connection settings in the application

## Usage
1. Enter a natural language question in the query input box
2. Click "Execute Query" to process your question
3. The system will generate and execute an SQL query
4. View the results in the table, chart, or summary tabs

## Security Note
This application is designed for development and internal use. It includes features that validate queries to prevent harmful operations, but additional security measures should be implemented for production environments.

## File Structure
- `index.php` - Main application file
- `assets/css/style.css` - Custom styling
- `assets/js/main.js` - Application logic

## License
This project is licensed under the MIT License.
