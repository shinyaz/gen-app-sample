FROM python:3.11
RUN mkdir /app

COPY requirements.txt /app/
RUN pip3 install --upgrade pip
RUN pip3 install -r /app/requirements.txt

COPY main.py /app/
ENTRYPOINT ["streamlit"]
CMD ["run", "app/main.py"]
EXPOSE 8501
