import { Link } from 'react-router-dom'

type ProjectCardprops = {
  id: number
  name: string
  description: string
  link?: string
}
function ProjectCard({id, name, description, link}: ProjectCardprops){
    return(
        <div className="project-card">
            <h3>{name}</h3>
            <p>{description}</p>
            {link ? <a href={link} target="_blank" rel="noreferrer">View Project</a> : <Link to={`/projects/${id}`}>View Project</Link>}
        </div>
    )

}
export default ProjectCard