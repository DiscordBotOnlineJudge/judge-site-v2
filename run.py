from dboj_site import app
import os

if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv("PORT")))
