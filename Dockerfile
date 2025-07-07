FROM python:3.12.3
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y net-tools
COPY . .
ENV PORT=8000
EXPOSE 8000
# Change the CMD to use a startup script
COPY startup.sh .
RUN chmod +x startup.sh
CMD ["./startup.sh"]