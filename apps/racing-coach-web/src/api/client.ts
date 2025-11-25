import Axios, { AxiosError, type AxiosRequestConfig } from "axios";

/**
 * Custom Axios instance configured with the API base URL.
 * Use this instance for any direct axios calls outside of generated hooks.
 */
export const axiosInstance = Axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
});

/**
 * Custom instance function for Orval-generated API calls.
 * This mutator unwraps the AxiosResponse so React Query hooks
 * return the data directly (e.g., `data: Session[]` instead of `data: AxiosResponse<Session[]>`).
 */
export const customInstance = <T>(
  config: AxiosRequestConfig,
  options?: AxiosRequestConfig
): Promise<T> => {
  const controller = new AbortController();

  const promise = axiosInstance({
    ...config,
    ...options,
    signal: controller.signal,
  }).then(({ data }) => data);

  // @ts-expect-error - Adding cancel method for React Query
  promise.cancel = () => {
    controller.abort("Query was cancelled");
  };

  return promise;
};

/**
 * Error type export for Orval to use in generated code.
 * This ensures proper error typing in React Query hooks.
 */
export type ErrorType<Error> = AxiosError<Error>;

/**
 * Body type export for Orval mutations.
 */
export type BodyType<Body> = Body;
