import Hero from '../components/Hero'
import Projects from '../components/Projects'
import Ideas from '../components/Ideas'
import Developers from '../components/Developers'
import CTA from '../components/CTA'
import Layout from '../components/Layout'

function Home() {
  return (
    <Layout>
      <Hero />
      <Projects />
      <Ideas />
      <Developers />
      <CTA />
    </Layout>
  )
}

export default Home