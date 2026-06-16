import { listExercises } from "@/lib/mock/admin-api";
import { ExercisesManager } from "./exercises-manager";

export const metadata = { title: "운동 종목" };

export default async function ExercisesPage() {
  const exercises = await listExercises();
  return <ExercisesManager initial={exercises} />;
}
