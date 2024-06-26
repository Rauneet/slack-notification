FROM python:3.8-slim
WORKDIR /usr/src/app
COPY . /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update -y
# removed EXPOSE since the script does not expose to web server
ENV CLICK_API_TOKEN=pk_73223342_17LY9UC6TE84D6P5MF2ALXU5W8UT6LHA
ENV SLACK_WEBHOOK_URL=https://hooks.slack.com/triggers/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
# We are running file_2.py here but now replace it with main.py
CMD ["python", "main.py"]  