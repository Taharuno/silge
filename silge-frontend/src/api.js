import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

export const getDashboard = () => api.get("/dashboard/");
export const getRecords = (params = {}) => api.get("/records/", { params });
export const getRecord = (id) => api.get(`/records/${id}`);
export const createRecord = (data) => api.post("/records/", data);
export const updateRecord = (id, data) => api.patch(`/records/${id}`, data);
export const approveDeletion = (id, approver) =>
  api.post(`/records/${id}/approve-deletion`, null, { params: { approver } });

export default api;
export const deleteRecord = (id, performedBy) => api.delete(`/records/${id}`, { params: { performed_by: performedBy } });
export const getAuditLogs = () => api.get("/audit/");
