# Render Amazon Order History

Takes the output of [order-history-exporter-for-amazon](https://github.com/xenolphthalein/order-history-exporter-for-amazon#usage) and shows it in a local website, to make matching Amazon orders against your bank and card transactions easier.

Everything runs on your own computer. Your order data is never uploaded anywhere.

## What you need

| Item | Windows 10/11 | Mac (macOS) |
|---|---|---|
| A web browser | Edge, Chrome or Firefox | Safari, Chrome or Firefox |
| **uv** (a free tool that installs Python and everything else for you) | Installed in step 2 | Installed in step 2 |
| An Amazon order export (`.json` file) | See step 3 | See step 3 |

You do **not** need to install Python yourself, and you do **not** need Git. Internet access is needed for the first setup only.

## Setup

### 1. Download this project

On this project's GitHub page, click the green **Code** button, then **Download ZIP**.

- **Windows:** right-click the downloaded ZIP and choose **Extract All**.
- **Mac:** double-click the downloaded ZIP.

Move the extracted folder somewhere easy to find, such as Documents. It is called `render-amazon-order-history` (it may have `-main` on the end).

### 2. Open a terminal and install uv

A terminal is a window where you type commands.

- **Windows:** press the Start key, type `PowerShell`, and press Enter.
- **Mac:** press Command + Space, type `Terminal`, and press Enter.

Copy the command for your computer, paste it into the terminal, and press Enter.

**Windows (PowerShell):**

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Mac:**

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

(If you use Homebrew, `brew install uv` also works.)

When it finishes, **close the terminal window and open a new one** so it can find uv. To check, type `uv --version`. You should see a version number.

### 3. Get your Amazon order export

Follow the [usage instructions](https://github.com/xenolphthalein/order-history-exporter-for-amazon#usage) of the exporter to download your orders. It produces a `.json` file, with a name like `amazon-orders-2026-10-11.json`.

Put that file in the `export-data` folder inside this project. If the folder does not exist, create it. You can add more than one `.json` file. They are combined, and if the same order is in two files, the file whose name sorts last is used.

Your export contains names and addresses, so keep that file private.

### 4. Start the website

In your terminal, go into the project folder:

1. Type `cd ` (the letters c, d and a space). Do not press Enter yet.
2. Drag the project folder from your file window onto the terminal window. This fills in the folder's location.
3. Press Enter.

Then run:

```
uv run uvicorn app.main:app
```

The first time, this takes a minute or two while it downloads what it needs. It is ready when you see a line saying `Uvicorn running on http://127.0.0.1:8000`.

### 5. Open the website

Open your browser and go to **http://127.0.0.1:8000**

### Stopping and starting again

- To stop: click the terminal window and press **Ctrl + C**, or just close the terminal.
- To start again later: repeat step 4 (the `cd` and the `uv run` lines) and step 5. You do not need to repeat steps 1 to 3.
- To load a new export: put the new `.json` file in `export-data` and refresh the page. No restart is needed.

## Using the website

- **Expand an order:** click its row to see the transaction (amount charged, savings, estimated tax and fees) and the items.
- **Sort:** click any column heading. Click again to reverse.
- **Search:** type an item name, ASIN, order ID or an amount such as `34.81`. Partial amounts like `34.8` work too.
- **Reconciled:** tick the box on an order to hide it once you have matched it. Use **Show reconciled** to bring those back. This is remembered only until you stop the website.
- **Currency:** by default every amount is shown in US dollars. The Amazon export sometimes labels orders with the wrong currency, such as euros on a $0.00 order. The currency menu lets you choose another currency, or show amounts as exported.

**Tax/fees (est.)** is the order total minus the item prices. It also includes any shipping or fees. It is shown only for orders with no promotions or savings. The export does not contain tax directly.

## If something goes wrong

| Problem | What to try |
|---|---|
| `uv` is not recognized or command not found | Close the terminal, open a new one, and try again. If it still fails, repeat step 2. |
| The page says no orders match | Check that a `.json` file is directly inside the `export-data` folder, not in a sub-folder. |
| "Address already in use" or port error | Something else is using that port. Run `uv run uvicorn app.main:app --port 8001` and open http://127.0.0.1:8001 instead. |
| The page will not load | Make sure the terminal is still open and running. |
| Windows says running scripts is disabled | Use the exact PowerShell command in step 2, which allows the install script to run once. |

## For developers

- Python 3.13 and [uv](https://docs.astral.sh/uv/). Run `uv sync` to install, `uv run pytest` to test.
- For auto-reload while editing: `uv run uvicorn app.main:app --reload`. Note that every reload clears the reconciled state.
- See `AGENTS.md` for the code layout and rules, and `BACKLOG.md` for planned work.
