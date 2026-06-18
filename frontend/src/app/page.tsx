import Link from "next/link";

const quickActions = [
  {
    number: "01",
    label: "Upload CSV",
    title: "Validasi laporan produksi",
    description:
      "Gunakan adapter untuk membaca CSV perusahaan, mendeteksi format, dan membentuk payload prediksi.",
    href: "/upload",
    tone: "light",
  },
  {
    number: "02",
    label: "Input Manual",
    title: "Prediksi tanpa file CSV",
    description:
      "Masukkan data produksi harian langsung dari form ketika user tidak memakai laporan batch.",
    href: "/manual",
    tone: "dark",
  },
  {
    number: "03",
    label: "Riwayat",
    title: "Pantau hasil prediksi",
    description:
      "Lihat status task, hasil estimasi WIP, dan proses rekonsiliasi setelah data aktual tersedia.",
    href: "/predictions",
    tone: "light",
  },
];

const workflowSteps = [
  {
    title: "Adapter membaca data",
    description:
      "CSV mentah dicek formatnya, lalu kolom yang relevan dipetakan ke kontrak input sistem.",
  },
  {
    title: "Payload dinormalisasi",
    description:
      "Data per tanggal dan profile disusun menjadi struktur yang aman untuk API prediksi.",
  },
  {
    title: "Model memprediksi WIP",
    description:
      "Artefak Extra Trees menghasilkan estimasi WIP ton berdasarkan fitur proses produksi.",
  },
  {
    title: "Hasil direkonsiliasi",
    description:
      "Prediksi dibandingkan dengan aktual untuk evaluasi error dan kebutuhan analisis lanjutan.",
  },
];

const modelSnapshot = [
  ["Model aktif", "Extra Trees"],
  ["Target", "WIP Ton"],
  ["Input", "CSV atau manual"],
  ["Output", "Estimasi WIP dan prime"],
];

export default function OverviewPage() {
  return (
    <div className="space-y-10">
      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <div className="relative overflow-hidden rounded-[2rem] border border-[#d7d2c5] bg-[#173a30] p-7 text-white shadow-[0_28px_70px_rgba(23,58,48,0.18)] sm:p-9">
          <div
            aria-hidden="true"
            className="absolute right-[-8rem] top-[-8rem] size-72 rounded-full bg-[#c65331]/25 blur-3xl"
          />

          <div className="relative max-w-3xl">
            <p className="badge-text text-xs font-bold text-[#eca88e]">
              Production Intelligence
            </p>

            <h1 className="mt-5 max-w-4xl text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
              Prediksi WIP produksi baja dari laporan harian.
            </h1>

            <p className="mt-5 max-w-2xl text-base leading-8 text-[#d8e5df] sm:text-lg">
              Sistem ini membantu QA/QC dan PPIC membaca data produksi,
              menjalankan prediksi WIP, lalu membandingkan hasil model
              dengan data aktual melalui rekonsiliasi.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/upload"
                className="rounded-2xl bg-[#c65331] px-5 py-3 text-center text-sm font-semibold text-white transition hover:bg-[#a94428]"
              >
                Mulai dari CSV
              </Link>

              <Link
                href="/predictions"
                className="rounded-2xl border border-white/20 px-5 py-3 text-center text-sm font-semibold text-white transition hover:bg-white/10"
              >
                Lihat riwayat prediksi
              </Link>
            </div>
          </div>
        </div>

        <aside className="rounded-[2rem] border border-[#d7d2c5] bg-white p-7 shadow-[0_20px_55px_rgba(32,45,38,0.06)]">
          <p className="badge-text text-xs font-bold text-[#c65331]">
            System Snapshot
          </p>

          <h2 className="mt-4 text-2xl font-semibold text-[#173a30]">
            Konfigurasi prediksi
          </h2>

          <div className="mt-6 space-y-4">
            {modelSnapshot.map(([label, value]) => (
              <div
                key={label}
                className="flex items-start justify-between gap-4 border-b border-[#ece7dc] pb-4 last:border-b-0 last:pb-0"
              >
                <p className="text-sm text-[#66736d]">{label}</p>
                <p className="value-text text-right text-sm font-semibold text-[#173a30]">
                  {value}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-6 rounded-2xl bg-[#f6f1e8] p-4">
            <p className="text-sm font-semibold text-[#173a30]">
              Catatan akademik
            </p>
            <p className="mt-2 text-sm leading-6 text-[#66736d]">
              Prediksi adalah estimasi model, bukan data aktual. Validasi
              akhir tetap dilakukan melalui proses rekonsiliasi.
            </p>
          </div>
        </aside>
      </section>

      <section>
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <p className="badge-text text-xs font-bold text-[#c65331]">
              Quick Actions
            </p>

            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-[#173a30]">
              Pilih alur kerja
            </h2>
          </div>

          <p className="max-w-xl text-sm leading-6 text-[#66736d]">
            Gunakan CSV untuk batch prediction, input manual untuk satu
            tanggal produksi, atau buka riwayat untuk melihat hasil dan
            rekonsiliasi.
          </p>
        </div>

        <div className="mt-6 grid gap-5 lg:grid-cols-3">
          {quickActions.map((action) => {
            const isDark = action.tone === "dark";

            return (
              <Link
                key={action.href}
                href={action.href}
                className={`group rounded-3xl border p-6 shadow-[0_18px_45px_rgba(32,45,38,0.05)] transition hover:-translate-y-1 ${
                  isDark
                    ? "border-[#173a30] bg-[#173a30] text-white"
                    : "border-[#d7d2c5] bg-white text-[#173a30] hover:border-[#c65331]"
                }`}
              >
                <div className="flex items-center justify-between gap-4">
                  <p
                    className={`value-text text-sm font-semibold ${
                      isDark ? "text-[#eca88e]" : "text-[#c65331]"
                    }`}
                  >
                    {action.number}
                  </p>

                  <span
                    className={`badge-text rounded-full px-3 py-1 text-xs font-bold ${
                      isDark
                        ? "bg-white/10 text-[#d8e5df]"
                        : "bg-[#f2eee5] text-[#66736d]"
                    }`}
                  >
                    {action.label}
                  </span>
                </div>

                <h3 className="mt-6 text-2xl font-semibold">
                  {action.title}
                </h3>

                <p
                  className={`mt-3 text-sm leading-7 ${
                    isDark ? "text-[#c8d8d1]" : "text-[#66736d]"
                  }`}
                >
                  {action.description}
                </p>

                <p
                  className={`mt-7 text-sm font-semibold ${
                    isDark ? "text-white" : "text-[#173a30]"
                  }`}
                >
                  Buka halaman {"->"}
                </p>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="rounded-[2rem] border border-[#d7d2c5] bg-white p-6 shadow-[0_20px_55px_rgba(32,45,38,0.06)] sm:p-7">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <p className="badge-text text-xs font-bold text-[#c65331]">
              Workflow
            </p>

            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-[#173a30]">
              Dari laporan mentah ke evaluasi aktual
            </h2>
          </div>

          <p className="max-w-xl text-sm leading-6 text-[#66736d]">
            Alur ini menjaga agar file yang tidak rapi tetap melewati
            validasi sebelum masuk ke model prediksi.
          </p>
        </div>

        <div className="mt-7 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {workflowSteps.map((step, index) => (
            <article
              key={step.title}
              className="rounded-2xl border border-[#ece7dc] bg-[#fbfaf6] p-5"
            >
              <p className="value-text text-sm font-semibold text-[#c65331]">
                {(index + 1).toString().padStart(2, "0")}
              </p>

              <h3 className="mt-4 text-lg font-semibold text-[#173a30]">
                {step.title}
              </h3>

              <p className="mt-3 text-sm leading-6 text-[#66736d]">
                {step.description}
              </p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
