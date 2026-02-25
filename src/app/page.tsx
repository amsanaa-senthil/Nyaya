import Hero from "@/components/Hero";
import Features from "@/components/Features";
import Team from "@/components/Team";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen bg-primary">
      <Hero />
      <Features />
      <Team />
      <Footer />
    </main>
  );
}
