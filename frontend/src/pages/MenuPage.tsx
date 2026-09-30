import Header from "../components/Header";
import Hero from "../components/Hero";
import SearchBox from "../components/SearchBox";
import DishesSection from "../components/DishesSection";

export default function MenuPage() {
  return (
    <div className="app">
      <Header/>
      <main className="main-content">
        <Hero />
        <SearchBox />
        <DishesSection />
      </main>
    </div>
  )
}