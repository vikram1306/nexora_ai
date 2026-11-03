'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  UploadCloud,
  Database,
  FileSpreadsheet,
  RefreshCw,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers
} from 'lucide-react';
import { ingestApi, DatasetItem, SchemaAnalysisResult } from '@/lib/api';
import { GlassCard } from '../ui/GlassCard';
import { DepartmentBadge } from '../ui/DepartmentBadge';
import { SchemaConfirmModal } from '../modals/SchemaConfirmModal';

interface IngestTabProps {
  datasets: DatasetItem[];
  onRefreshDatasets: () => void;
  onDatasetUploaded?: () => void;
}

export function IngestTab({
  datasets,
  onRefreshDatasets,
  onDatasetUploaded,
}: IngestTabProps) {
  const [selectedDept, setSelectedDept] = useState('sales');
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Background Job Progress state
  const [jobProgress, setJobProgress] = useState<{
    jobId: string;
    progress: number;
    stage: string;
    status: string;
  } | null>(null);

  // Schema intelligence modal state
  const [schemaProposal, setSchemaProposal] = useState<SchemaAnalysisResult | null>(null);
  const [isConfirmingSchema, setIsConfirmingSchema] = useState(false);

  const departments = [
    { id: 'sales', label: 'Sales Department' },
    { id: 'finance', label: 'Finance Department' },
    { id: 'hr', label: 'HR Department' },
    { id: 'marketing', label: 'Marketing Department' },
    { id: 'operations', label: 'Operations Department' },
  ];

  // Background Job Polling
  const pollJob = (jobId: string, dept: string) => {
    const interval = setInterval(async () => {
      try {
        const job = await ingestApi.getJobStatus(jobId);
        setJobProgress({
          jobId: job.id,
          progress: job.progress || 0,
          stage: job.stage || 'Processing dataset chunks...',
          status: job.status,
        });

        if (job.status === 'COMPLETED') {
          clearInterval(interval);
          setIsUploading(false);
          setIsConfirmingSchema(false);
          setUploadSuccess(
            `Successfully ingested '${job.filename}' (${(
              job.row_count || 0
            ).toLocaleString()} rows) into ${dept.toUpperCase()} Enterprise Memory!`
          );
          setFileToUpload(null);
          setSchemaProposal(null);
          onRefreshDatasets();
          if (onDatasetUploaded) onDatasetUploaded();
          setTimeout(() => setJobProgress(null), 4000);
        } else if (job.status === 'FAILED') {
          clearInterval(interval);
          setIsUploading(false);
          setIsConfirmingSchema(false);
          setErrorMessage(job.error_message || 'Ingestion job failed in background queue.');
          setTimeout(() => setJobProgress(null), 4000);
        }
      } catch (err) {
        // Retry polling on transient network issue
      }
    }, 450);
  };

  // Inspect & Propose Schema Mapping
  const handleAnalyzeSchema = async () => {
    if (!fileToUpload) {
      setErrorMessage('Please select a CSV file first.');
      return;
    }

    setIsUploading(true);
    setUploadSuccess('');
    setErrorMessage('');

    try {
      const proposal = await ingestApi.analyzeSchema(fileToUpload, selectedDept);
      setSchemaProposal(proposal);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to analyze CSV schema.');
    } finally {
      setIsUploading(false);
    }
  };

  // Confirm Schema Mapping and Ingest
  const handleConfirmMapping = async (confirmedMapping: Record<string, string>) => {
    if (!schemaProposal) return;
    setIsConfirmingSchema(true);
    setErrorMessage('');

    try {
      const job = await ingestApi.confirmAndIngest(
        schemaProposal.temp_file_id,
        schemaProposal.department,
        confirmedMapping
      );

      setJobProgress({
        jobId: job.id,
        progress: job.progress || 10,
        stage: job.stage || 'Queued in background worker pool',
        status: job.status,
      });

      setSchemaProposal(null);
      pollJob(job.id, selectedDept);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error confirming schema mapping.');
      setIsConfirmingSchema(false);
    }
  };

  // Direct Upload (Quick Ingest)
  const handleDirectUpload = async () => {
    if (!fileToUpload) {
      setErrorMessage('Please select a CSV file first.');
      return;
    }

    setIsUploading(true);
    setUploadSuccess('');
    setErrorMessage('');

    try {
      const job = await ingestApi.uploadDirect(fileToUpload, selectedDept);
      setJobProgress({
        jobId: job.id,
        progress: job.progress || 10,
        stage: job.stage || 'Queued in background worker pool',
        status: job.status,
      });
      pollJob(job.id, selectedDept);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to upload CSV file.');
      setIsUploading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8"
    >
      <div>
        <h1 className="text-3xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
          <UploadCloud className="w-8 h-8 text-accent-cyan" /> Enterprise Memory Ingestion
        </h1>
        <p className="text-neutral-400 text-sm font-light mt-1">
          Upload CSV department datasets. Automatic schema profiling, KPI extraction, and ChromaDB vector indexing.
        </p>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-accent-rose/10 border border-accent-rose/30 text-accent-rose text-xs flex items-center gap-3">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Datasets Active in Enterprise Memory */}
      <GlassCard className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-serif font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-accent-cyan" /> Active Ingested Datasets in Memory ({datasets.length})
          </h2>
          <button
            onClick={onRefreshDatasets}
            className="px-3 py-1.5 rounded-lg bg-obsidian-850 hover:bg-white/10 border border-white/10 text-xs text-neutral-300 transition-all flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh List
          </button>
        </div>

        {datasets.length === 0 ? (
          <div className="p-8 rounded-xl bg-obsidian-850/50 border border-white/5 text-center text-xs text-neutral-400 font-light">
            No datasets currently ingested. Select a CSV below to populate relational SQL tables and ChromaDB semantic memory.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-neutral-400 font-mono uppercase text-[10px]">
                  <th className="py-3 px-4">Dataset Name</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4">Row Count</th>
                  <th className="py-3 px-4">Primary KPI Detected</th>
                  <th className="py-3 px-4">Memory Index Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {datasets.map((ds) => (
                  <tr key={ds.id} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 px-4 font-semibold text-white flex items-center gap-2">
                      <FileSpreadsheet className="w-4 h-4 text-accent-cyan flex-shrink-0" />
                      <span className="truncate max-w-xs">{ds.name}</span>
                    </td>
                    <td className="py-3 px-4">
                      <DepartmentBadge department={ds.department} size="xs" />
                    </td>
                    <td className="py-3 px-4 font-mono text-neutral-200">
                      {(ds.row_count || 0).toLocaleString()} rows
                    </td>
                    <td className="py-3 px-4 text-neutral-300 font-mono">
                      {ds.schema_info?.kpis_extracted?.primary_metric || 'Analyzed & Profiled'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/30 font-semibold text-[10px] font-mono">
                        <span className="w-1.5 h-1.5 rounded-full bg-accent-emerald animate-pulse" />{' '}
                        Indexed &amp; Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>

      {/* Upload Box */}
      <GlassCard className="p-8 max-w-2xl mx-auto space-y-6">
        <h2 className="text-lg font-serif font-bold text-white flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-accent-cyan" /> Upload New Department Dataset
        </h2>

        <div>
          <label className="block text-xs font-mono uppercase text-neutral-400 mb-2 font-semibold">
            Target Department
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {departments.map((d) => (
              <button
                key={d.id}
                type="button"
                onClick={() => setSelectedDept(d.id)}
                className={`p-2.5 rounded-xl border text-xs font-semibold transition-all text-left ${
                  selectedDept === d.id
                    ? 'bg-accent-cyan/15 border-accent-cyan text-white shadow-sm'
                    : 'bg-obsidian-850 border-white/5 text-neutral-400 hover:text-white hover:border-white/15'
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {/* Dropzone */}
        <div className="border-2 border-dashed border-white/15 rounded-2xl p-8 text-center hover:border-accent-cyan/50 transition-all cursor-pointer relative bg-obsidian-850/40">
          <UploadCloud className="w-10 h-10 text-accent-cyan mx-auto mb-3" />
          <p className="text-sm font-medium text-white mb-1">
            {fileToUpload ? fileToUpload.name : 'Click or select CSV file to ingest'}
          </p>
          <p className="text-xs text-neutral-500">Supports CSV files up to 100,000+ rows</p>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFileToUpload(e.target.files?.[0] || null)}
            className="mt-4 text-xs text-neutral-400 mx-auto block cursor-pointer"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <button
            type="button"
            onClick={handleAnalyzeSchema}
            disabled={isUploading || isConfirmingSchema}
            className="w-full sm:flex-1 py-3.5 rounded-xl bg-accent-cyan text-obsidian-950 font-bold text-xs hover:brightness-110 transition-all shadow-lg shadow-accent-cyan/20 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isUploading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            Inspect &amp; Confirm AI Schema Mapping
          </button>

          <button
            type="button"
            onClick={handleDirectUpload}
            disabled={isUploading || isConfirmingSchema}
            className="w-full sm:w-auto px-5 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 text-white font-semibold text-xs transition-all disabled:opacity-50"
            title="Ingest directly with AI auto-inferred schema"
          >
            Quick Ingest
          </button>
        </div>

        {/* Streaming Ingestion Progress Bar */}
        {jobProgress && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-5 rounded-xl bg-obsidian-850 border border-accent-cyan/40 space-y-3 shadow-xl"
          >
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-white flex items-center gap-2 font-mono">
                <RefreshCw className="w-3.5 h-3.5 text-accent-cyan animate-spin" />
                {jobProgress.stage}
              </span>
              <span className="font-mono text-accent-cyan font-bold">{jobProgress.progress}%</span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-accent-cyan to-accent-emerald h-full transition-all duration-300 ease-out"
                style={{ width: `${jobProgress.progress}%` }}
              />
            </div>
            <div className="text-[11px] text-neutral-400 flex items-center justify-between font-mono">
              <span>Async Worker Queue: Streaming Chunk Profiler</span>
              <span className="text-accent-cyan uppercase">{jobProgress.status}</span>
            </div>
          </motion.div>
        )}

        {uploadSuccess && (
          <div className="p-4 rounded-xl bg-accent-emerald/10 border border-accent-emerald/30 text-accent-emerald text-xs flex items-center gap-2 font-mono">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>{uploadSuccess}</span>
          </div>
        )}
      </GlassCard>

      {/* Schema Confirmation Modal */}
      {schemaProposal && (
        <SchemaConfirmModal
          proposal={schemaProposal}
          onConfirm={handleConfirmMapping}
          onCancel={() => setSchemaProposal(null)}
          isConfirming={isConfirmingSchema}
        />
      )}
    </motion.div>
  );
}

