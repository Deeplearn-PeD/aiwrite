FROM ubuntu:23.04

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1

# to run poetry directly as soon as it's installed
ENV PATH="$POETRY_HOME/bin:$PATH"
ENV PGURL="postgresql://postgres:eueueu@db:5432/platform"

RUN apt-get update && apt-get install -y python3 python3-pip curl git
RUN apt-get install -y build-essential ca-certificates
RUN apt-get install -y libmpv2
RUN ln -s /usr/lib/x86_64-linux-gnu/libmpv.so.2 /usr/lib/x86_64-linux-gnu/libmpv.so.1
RUN apt-get install -y sox uvicorn

# Change shell to bash
SHELL ["/bin/bash", "-c"]

RUN useradd -m libby
RUN usermod -aG sudo libby

RUN curl -sSL https://install.python-poetry.org | python3 -

#USER libby

COPY pyproject.toml .
COPY poetry.lock .
COPY requirements.txt .
COPY libbygui /libbygui/
COPY ./Docker/poetry_install.sh /scripts/poetry_install.sh
COPY ./Docker/entrypoint.sh /scripts/entrypoint.sh


RUN /scripts/poetry_install.sh

RUN . .venv/bin/activate

#RUN pip install git+https://github.com/Deeplearn-PeD/base-ai-agent.git --break-system-packages
#RUN pip install --no-cache-dir -U -r requirements.txt --break-system-packages
#RUN pip install --no-cache-dir -U flet --break-system-packages
#RUN pip install --no-cache-dir -U git+https://github.com/Deeplearn-PeD/libby.git@main --break-system-packages

ENTRYPOINT ["/bin/bash","-c","/scripts/entrypoint.sh"]
#CMD ["uvicorn", "libbygui.main:run", "--host", "0.0.0.0", "--port", "8860"]




