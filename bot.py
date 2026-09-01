import asyncio
import io
import logging
import re
from PIL import Image, ImageDraw, ImageFont
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Masukkan Token Bot Telegram Kamu
TOKEN = "8834039237:AAGheXsBM3miEmAXnd9f_mJbtl6vJBkBjZo"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def format_nomor(nomor_raw):
    angka = re.sub(r"\D", "", nomor_raw)
    if angka.startswith("62"):
        angka = "0" + angka[2:]
    match = re.match(r"^(\d{4})(\d{4})(\d{4,5})$", angka)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return angka


def generate_image_bytes(nomor_formatted):
    # Membuka template dan menggambar teks
    img = Image.open("template.png")
    draw = ImageDraw.Draw(img)
    UKURAN_FONT = 54

    try:
        font = ImageFont.truetype("font.ttf", UKURAN_FONT)
    except Exception:
        font = ImageFont.load_default()

    posisi_x = 1295
    posisi_y = 720
    warna_teks = (0, 0, 0)

    draw.text(
        (posisi_x, posisi_y), nomor_formatted, fill=warna_teks, font=font
    )

    # Simpan ke memory buffer (RAM) agar aman & cepat di server Railway
    bio = io.BytesIO()
    bio.name = "output.png"
    img.save(bio, "PNG")
    bio.seek(0)
    return bio


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "<b>SYSTEM GENERATOR LAPORAN</b>\n"
        "━━━━━━━ ✦ ━━━━━━━\n\n"
        "<blockquote>Silakan kirimkan nomor telepon/ID yang ingin dimasukkan ke dalam tabel laporan.</blockquote>\n\n"
        "<i>Format otomatis: <code>0000-0000-0000</code></i>"
    )
    await update.message.reply_text(caption, parse_mode=ParseMode.HTML)


async def process_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # 1. Loading Step 1
    status_msg = await update.message.reply_text(
        "<b>[■□□□□□□□□□] 10%</b>\n<i>Validasi format nomor...</i>",
        parse_mode=ParseMode.HTML,
    )

    nomor_hasil = format_nomor(user_text)
    await asyncio.sleep(0.3)

    # 2. Loading Step 2
    await status_msg.edit_text(
        f"<b>[■■■■■□□□□□] 50%</b>\n<i>Menempelkan nomor <code>{nomor_hasil}</code> ke template...</i>",
        parse_mode=ParseMode.HTML,
    )

    try:
        # Generate gambar langsung via memory BytesIO
        image_bytes = generate_image_bytes(nomor_hasil)
        await asyncio.sleep(0.3)

        # 3. Loading Step 3
        await status_msg.edit_text(
            "<b>[■■■■■■■■■■] 100%</b>\n<i>Menyelesaikan rendering gambar...</i>",
            parse_mode=ParseMode.HTML,
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Input Nomor Lain", callback_data="reset"
                ),
                InlineKeyboardButton("🗑️ Hapus Pesan", callback_data="delete"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        caption_gambar = (
            "<b>LAPORAN BERHASIL DIPROSES</b>\n"
            "━━━━━━━ ✦ ━━━━━━━\n"
            f"<b>Nomor Terpilih:</b> <code>{nomor_hasil}</code>\n"
            "<b>Status:</b> <code>Menunggu Verifikasi</code>\n"
            "━━━━━━━ ✦ ━━━━━━━"
        )

        await update.message.reply_photo(
            photo=image_bytes,
            caption=caption_gambar,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )

        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error processing image: {e}")
        await status_msg.edit_text(f"❌ <b>Gagal memproses gambar:</b> {e}")


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "reset":
        await query.message.reply_text(
            "<b>Silakan masukkan nomor baru:</b>", parse_mode=ParseMode.HTML
        )
    elif query.data == "delete":
        await query.message.delete()


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), process_number)
    )
    app.add_handler(CallbackQueryHandler(button_click))

    print("Bot sedang berjalan...")
    app.run_polling()
