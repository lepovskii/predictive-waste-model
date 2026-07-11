"use client";

import { useEffect, useState } from "react";
import { getAvailableModels, switchActiveModel } from "@/lib/api-client";
import type { ModelArtifact } from "@/types/models";

export default function ModelsPage() {
    const [models, setModels] = useState<ModelArtifact[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSwitching, setIsSwitching] = useState(false);
    const [message, setMessage] = useState("");

    useEffect(() => {
        getAvailableModels()
            .then((res) => {
                setModels(res.models);
            })
            .catch((err) => {
                console.error(err);
                setMessage("Gagal memuat daftar model");
            })
            .finally(() => {
                setIsLoading(false);
            });
    }, []);

    async function handleSwitch(artifactId: string) {
        setIsSwitching(true);
        setMessage("");
        try {
            const response = await switchActiveModel(artifactId);
            setMessage(response.message);

            const updatedResponse = await getAvailableModels();
            setModels(updatedResponse.models);
            window.location.reload();
        } catch (error) {
            console.error(error);
            setMessage("Gagal mengganti model");
        } finally {
            setIsSwitching(false);
        }
    }

    return (
        <div className="space-y-6 max-w-5xl mx-auto py-8">
            <header className="bg-white p-8 rounded-3xl border border-[#d7d2c5] shadow-[0_18px_45px_rgba(32,45,38,0.06)]">
                <h1 className="text-3xl font-semibold text-[#173a30]">Model Manager</h1>
                <p className="text-base text-[#66736d] mt-2">
                    Pilih model machine learning yang aktif untuk sistem prediksi. Perubahan di sini akan memengaruhi adapter CSV dan mengubah UI form input manual secara otomatis.
                </p>
            </header>

            {message && (
                <div className="p-4 bg-[#e8f5e9] text-[#2e7d32] rounded-xl font-medium border border-[#c8e6c9]">
                    {message}
                </div>
            )}

            {isLoading ? (
                <p className="text-center text-[#66736d] py-10 animate-pulse">Memuat metadata model dari backend...</p>
            ) : (
                <div className="grid gap-6 md:grid-cols-2">
                    {models.map((model) => (
                        <div
                            key={model.artifact_id}
                            className={`p-6 rounded-3xl border ${model.is_active ? 'border-[#c65331] bg-[#fff9f7] ring-4 ring-[#c65331]/10' : 'border-[#d7d2c5] bg-white'} shadow-[0_18px_45px_rgba(32,45,38,0.06)] flex flex-col justify-between`}
                        >
                            <div>
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <span className={`text-xs font-bold uppercase tracking-wider ${model.is_active ? 'text-[#c65331]' : 'text-gray-500'}`}>
                                            {model.is_active ? 'Model Sedang Aktif' : 'Tersedia'}
                                        </span>
                                        <h2 className="text-xl font-semibold text-[#173a30] mt-1 break-all">
                                            {model.folder_name}
                                        </h2>
                                    </div>
                                </div>

                                <div className="space-y-2 text-sm text-[#33473e] mb-6 p-4 bg-[#faf9f5] rounded-2xl border border-[#dedbd1]">
                                    <p><strong>Target:</strong> {model.metadata.target} {model.metadata.target_transform ? `(${model.metadata.target_transform})` : ''}</p>
                                    <p><strong>Algorithm:</strong> {model.metadata.algorithm}</p>
                                    <p><strong>Total Input:</strong> {model.metadata.features.all_input_columns.length} fitur / kolom</p>
                                    <p className="pt-2 mt-2 border-t border-[#e5e1d7] text-xs text-[#66736d]">
                                        {model.metadata.model_purpose}
                                    </p>
                                </div>
                            </div>

                            <button
                                onClick={() => handleSwitch(model.artifact_id)}
                                disabled={model.is_active || isSwitching}
                                className={`w-full py-3 px-4 rounded-xl font-semibold text-sm transition ${model.is_active
                                    ? 'bg-[#efeee8] text-[#a1aaa5] cursor-not-allowed'
                                    : 'bg-[#173a30] text-white hover:bg-[#204d41] shadow-lg hover:shadow-xl hover:-translate-y-0.5'
                                    }`}
                            >
                                {isSwitching && !model.is_active ? "Memproses pergantian..." : model.is_active ? "Status: AKTIF" : "Aktifkan Model Ini"}
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
