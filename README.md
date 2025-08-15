# **BOTIFY** - DISCORD AI & MUSIC BOT 🤖🎧

![botify](.\images\botify_banner.png)

Botify is a feature-rich Discord bot that combines OpenAI-powered conversation with music playback, server utilities, and role management.
It can respond to chat messages with AI, play music from YouTube, manage polls, assign/remove roles, and more — all in one bot.

# FEATURES

## 🎵 Music Playback

Use the following slash commands in your discord server:

- `/play [song name]` — Plays an audio from YouTube or adds it to the queue.
- `/pause` — Pauses the current song.
- `/resume` — Resumes paused playback.
- `/skip` — Skips the current song.
- `/stop` — Bot disconnects from the voice channel.

## 🧠 AI Chatbot

- Uses *OpenAI GPT-4o-mini* to respond to user messages directly in chat.
- Provides short and concrete answers.

## 🔧 Server Utility Commands

- `/assign [role]` — Assigns a role to the user.
- `/remove [role]` — Removes a role from the user.
- `/poll [question]` — Creates a *yes/no* poll with reactions.
- `/clear-chat` — Clears the channel if the user has the role *admin*.
- `/datetime` — Shows current time.

## 📢 Event Handling

- Welcomes new members.
- All bot events are logged in `discord.log` file for debugging.

# USAGE OPTIONS

## **Option 1 — Add Botify directly to your server**

You can invite Botify to your server using this link:

[➕ Invite Botify](https://discord.com/oauth2/authorize?client_id=1404709155511730277&permissions=603552491110224&integration_type=0&scope=bot+applications.commands)

Required permissions:

- Manage Roles (for `/assign` and `/remove`)
- Connect & Speak (for music playback)
- Read & Send Messages
- Manage Messages (for `/clear-chat`)

Once added, Botify will be available instantly.

## **Option 2 — Self-Host Your Own Bot Instance**

You can create your own bot and use your own API keys.

## 📦 Requirements

- **uv** (for dependency management) → [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.8+

## ⚙ Setup

In [Discord Developer Portal](https://discord.com/developers/applications), log in and create a new application. You can customize your own bot.
In the OAuth2 window, you should give the following permissions:

- **Scopes**:
  - applications.commands
  - bot

- **Bot permissions**: You can give administrator or the following ones
  - View channels
  - All of Text permissions
  - Connect
  - Speak

### Installation

- Clone the project:

```bash
git clone https://github.com/adriapc/botify-discord.git
cd botify-discord
```

- Install dependencies with *uv*:

```bash
uv sync
```

### Create `.env` file

```env
DISCORD_TOKEN=your_discord_bot_token
OPENAI_TOKEN=your_openai_api_key
GUILD_ID=your_discord_server_id
```

Where to get these:

- Discord Bot Token: [Discord Developer Portal](https://discord.com/developers/applications)
- OpenAI API Key: [OpenAI API Platform](https://platform.openai.com/docs/overview)
- Guild ID: right-click your server → “Copy Server ID” (Developer Mode must be enabled).

### Run the file

```bash
uv run main.py
```

If everything is correct, you should see:

```bash
Botify is ready
Synced X commands to guild <guild_id>
```
