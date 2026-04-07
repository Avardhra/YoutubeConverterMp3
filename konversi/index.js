const path = require('path');
const fs = require('fs').promises;
const libre = require('libreoffice-convert');
const util = require('util');

// Mengubah fungsi convert menjadi versi Promise agar bisa pakai async/await
const convertAsync = util.promisify(libre.convert);

async function main() {
    const inputDir = path.join(__dirname, 'input');
    const outputDir = path.join(__dirname, 'output');

    try {
        // 1. Pastikan folder output ada
        await fs.mkdir(outputDir, { recursive: true });

        // 2. Baca semua file di folder input
        const files = await fs.readdir(inputDir);
        const pptxFiles = files.filter(f => f.toLowerCase().endsWith('.pptx'));

        if (pptxFiles.length === 0) {
            console.log("❌ Tidak ada file .pptx di folder 'input'!");
            return;
        }

        console.log(`🚀 Menemukan ${pptxFiles.length} file. Memulai konversi...\n`);

        for (const fileName of pptxFiles) {
            const inputPath = path.join(inputDir, fileName);
            const outputName = fileName.replace('.pptx', '.pdf');
            const outputPath = path.join(outputDir, outputName);

            console.log(`⏳ Sedang memproses: ${fileName}...`);

            // Baca file PPTX
            const docxBuf = await fs.readFile(inputPath);

            // Konversi ke PDF menggunakan LibreOffice
            // undefined di sini artinya kita pakai filter default untuk PDF
            let pdfBuf = await convertAsync(docxBuf, '.pdf', undefined);

            // Simpan hasil
            await fs.writeFile(outputPath, pdfBuf);
            console.log(`✅ Selesai: ${outputName}`);
        }

        console.log("\n✨ Semua file berhasil dikonversi! Cek folder 'output'.");

    } catch (err) {
        console.error("\n🔴 Terjadi kesalahan:");
        console.error(err.message);
        if (err.message.includes('LibreOffice')) {
            console.log("Tip: Pastikan LibreOffice sudah terinstall di sistem kamu.");
        }
    }
}

main();