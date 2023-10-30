Riki is the version that is modified to be executed from Ubuntu server. 
You can use PyCharm and command line tools to start the Flask/Wiki system with “python Riki.py”.
You can access the wiki [http://wiki440.ms2ms.com](http://wiki440.ms2ms.com).

## Configuration
    
1. Update CONTENT_DIR and USER_DIR in config.py. 
    * CONTENT_DIR should point to the directory where your `content' is located.
    * USER_DIR should point to the directory where your `user' is located.
2. When you want to use login, make PRIVATE = True in config.py. Remember you can use id "name" and password "1234".
3. Always use virtualenv and pip.
    * pip install -r requirements.txt
