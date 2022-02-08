from dboj_site import app
import os

if __name__ == '__main__':
    app.run(debug=False, port=int(os.getenv("PORT")))
