import { listExercises } from "@/lib/api/admin-exercises";
import { ExercisesManager } from "./exercises-manager";

export const metadata = { title: "운동 종목" };

export default async function ExercisesPage() {
  const exercises = await listExercises();
  return <ExercisesManager initial={exercises} />;
}
