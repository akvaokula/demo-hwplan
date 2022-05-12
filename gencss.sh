if [[ FLASK_ENV = "development" ]]
then npx tailwindcss -i static/src/style.css -o static/css/main.css --watch
else npx tailwindcss -i static/src/style.css -o static/css/main.css
fi
