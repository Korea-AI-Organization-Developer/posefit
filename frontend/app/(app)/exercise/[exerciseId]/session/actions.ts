"use server";

export async function logVideoFile(filename: string, sizeBytes: number) {
  console.log("[녹화 영상]", filename, `(${sizeBytes} bytes)`);
}
