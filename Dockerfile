FROM ubuntu:23.04

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1

# to run poetry directly as soon as it's installed
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update && apt-get install -y python3 python3-pip curl git
RUN apt-get install -y build-essential
RUN apt-get install -y libmpv2
RUN ln -s /usr/lib/x86_64-linux-gnu/libmpv.so.2 /usr/lib/x86_64-linux-gnu/libmpv.so.1
RUN apt-get install -y sox uvicorn

#RUN curl -sSL https://install.python-poetry.org | python3 -


COPY requirements.txt .
COPY libbygui /libbygui/

RUN pip install git+https://github.com/Deeplearn-PeD/base-ai-agent.git --break-system-packages
RUN pip install --no-cache-dir -U -r requirements.txt --break-system-packages
#RUN pip install --no-cache-dir -U flet --break-system-packages
#RUN pip install --no-cache-dir -U git+https://github.com/Deeplearn-PeD/libby.git@main --break-system-packages


CMD ["uvicorn", "libbygui.main:app", "--host", "0.0.0.0", "--port", "7860"]




