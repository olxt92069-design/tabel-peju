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


def generate_image(nomor_formatted):
    img = Image.open("template.png")
    draw = ImageDraw.Draw(img)
    UKURAN_FONT = 52

    # Memuat font lokal font.ttf agar posisi presisi di Railway & Termux
    try:
        font = ImageFont.truetype("font.ttf", UKURAN_FONT)
    except IOError:
        font = ImageFont.load_default()

    posisi_x = 1295
    posisi_y = 720
    warna_teks = (0, 0, 0)

    draw.text(
        (posisi_x, posisi_y), nomor_formatted, fill=warna_teks, font=font
    )

    output_path = "output.png"
    img.save(output_path)
    return output_path


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
    nomor_hasil = format_nomor(user_text)

    status_msg = await update.message.reply_text(
        f"<b>PROCESSING DATA...</b>\nNomor: <code>{nomor_hasil}</code>",
        parse_mode=ParseMode.HTML,
    )

    try:
        image_path = generate_image(nomor_hasil)

        keyboard = [
            [InlineKeyboardButton("Input Nomor Lain", callback_data="reset")]
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
            photo=open(image_path, "rb"),
            caption=caption_gambar,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Gagal memproses gambar:</b> {e}")


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "reset":
        await query.message.reply_text(
            "<b>Silakan masukkan nomor baru:</b>", parse_mode=ParseMode.HTML
        )


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), process_number)
    )
    app.add_handler(CallbackQueryHandler(button_click))

    print("Bot sedang berjalan...")
    app.run_polling()
