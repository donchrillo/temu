import axios from 'axios';
import type { ConvertResponse, FileListResponse, OpAnalysisResponse } from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const filesApi = {
  listOrders: (): Promise<FileListResponse> =>
    apiClient.get('/api/files/orders').then((res) => res.data),
  listPayments: (): Promise<FileListResponse> =>
    apiClient.get('/api/files/payments').then((res) => res.data),
  uploadOrder: (file: File): Promise<{ status: string; filename: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient
      .post('/api/files/orders/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((res) => res.data);
  },
  uploadPayment: (file: File): Promise<{ status: string; filename: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient
      .post('/api/files/payments/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((res) => res.data);
  },
  getOrderContent: (filename: string): Promise<{ status: string; filename: string; content: string }> =>
    apiClient.get(`/api/files/orders/${encodeURIComponent(filename)}/content`).then((res) => res.data),
  saveOrderContent: (filename: string, content: string): Promise<{ status: string; filename: string }> =>
    apiClient.put(`/api/files/orders/${encodeURIComponent(filename)}/content`, { content }).then((res) => res.data),
  getPaymentContent: (filename: string): Promise<{ status: string; filename: string; content: string }> =>
    apiClient.get(`/api/files/payments/${encodeURIComponent(filename)}/content`).then((res) => res.data),
  savePaymentContent: (filename: string, content: string): Promise<{ status: string; filename: string }> =>
    apiClient.put(`/api/files/payments/${encodeURIComponent(filename)}/content`, { content }).then((res) => res.data),
};

export const convertApi = {
  orders: (files: string[]): Promise<ConvertResponse> =>
    apiClient.post('/api/convert/orders', { files }).then((res) => res.data),
  payments: (files: string[]): Promise<ConvertResponse> =>
    apiClient.post('/api/convert/payments', { files }).then((res) => res.data),
};

export const opApi = {
  analyze: (): Promise<OpAnalysisResponse> =>
    apiClient.post('/api/op/analyze').then((res) => res.data),
};

export const exportsApi = {
  list: (): Promise<FileListResponse> =>
    apiClient.get('/api/exports').then((res) => res.data),
  getContent: (filename: string): Promise<{ status: string; filename: string; content: string }> =>
    apiClient.get(`/api/exports/${encodeURIComponent(filename)}/content`).then((res) => res.data),
  downloadUrl: (filename: string): string =>
    `${API_BASE_URL}/api/exports/${encodeURIComponent(filename)}`,
};

export default apiClient;
