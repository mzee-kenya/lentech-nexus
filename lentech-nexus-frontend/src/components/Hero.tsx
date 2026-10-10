import { Link } from 'react-router-dom'
import './Hero.css'
function Hero(){
    return(
        <div className="hero">
            <h1>Lentech Nexus</h1>
            <h2>Ideas Connect. People Collaborate. Solutions Grow.</h2>
            <Link to="/projects" className="hero-link">Explore Projects</Link>
             <Link to="/ideas/new" className="hero-link">Share an Idea</Link>
        </div>
    )
}
export default Hero