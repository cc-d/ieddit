FROM python:3

WORKDIR /usr/src/app

# Copy all files into /usr/src/app
COPY . .

# Replace URL in config.py with "URL = ${URL}" at line 25
RUN sed -i "25s/.*/URL = 'http:\/\/localhost:3000'/" config.py

# Replace DB_TYPE in config.py with "DB_TYPE = 'sqlite'" at line 9
RUN sed -i "9s/.*/DB_TYPE = 'sqlite'/" config.py

RUN chmod +x ./install.sh

# Run install script
RUN ./install.sh -y

CMD python3 create_db.py && python3 run.py
