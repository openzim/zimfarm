import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

export default function httpRequest(
  httpProps: Pick<AxiosRequestConfig, 'baseURL' | 'headers'>,
): AxiosInstance {
  const { baseURL, headers } = httpProps
  const http = axios.create({
    baseURL,
    timeout: 30000, // timeout of 30 seconds
    headers: {
      ...headers,
      'Content-Type': 'application/json',
    },
    withCredentials: true,
    paramsSerializer: {
      indexes: null, // This prevents the [] notation in array parameters
    },
  })

  // use request interceptors
  http.interceptors.request.use(
    (config) => {
      return config
    },
    (error) => {
      return Promise.reject(error)
    },
  )

  http.interceptors.response.use(
    (response) => {
      return response.data
    },
    (error) => {
      return Promise.reject((error.response && error.response.data) || error.response || error)
    },
  )

  return http
}
