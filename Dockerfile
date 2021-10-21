FROM gorialis/discord.py:minimal

WORKDIR /a-discord-bot

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]