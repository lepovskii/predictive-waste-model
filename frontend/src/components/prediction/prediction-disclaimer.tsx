export function PredictionDisclaimer() {
  return (
    <div
      role="note"
      className="mt-6 rounded-2xl border border-[#dfc98d] bg-[#fff8df] p-4 text-[#674e0b]"
    >
      <p className="text-sm font-semibold">
        Tentang hasil prediksi
      </p>

      <p className="mt-1 text-xs leading-5">
        Nilai WIP merupakan estimasi model berdasarkan data proses
        produksi, bukan nilai aktual. Hasil dapat berbeda dari kondisi
        sebenarnya dan tetap perlu diverifikasi melalui proses
        rekonsiliasi.
      </p>
    </div>
  );
}