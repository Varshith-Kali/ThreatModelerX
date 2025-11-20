import { BookOpen, Shield, Code, Lock, AlertTriangle, ExternalLink, GraduationCap, FileText } from 'lucide-react';

export default function TrainingSection() {
  const bestPractices = [
    {
      id: 1,
      title: "Input Validation",
      description: "Always validate and sanitize all user inputs to prevent injection attacks.",
      icon: Shield,
      link: "https:
      color: "text-purple-400"
    },
    {
      id: 2,
      title: "Authentication & Authorization",
      description: "Implement strong authentication and proper authorization checks.",
      icon: Lock,
      link: "https:
      color: "text-blue-400"
    },
    {
      id: 3,
      title: "Secure Data Storage",
      description: "Encrypt sensitive data at rest and in transit. Never store secrets in code.",
      icon: Code,
      link: "https:
      color: "text-green-400"
    },
    {
      id: 4,
      title: "Dependency Management",
      description: "Regularly update dependencies and scan for vulnerabilities.",
      icon: AlertTriangle,
      link: "https:
      color: "text-yellow-400"
    },
    {
      id: 5,
      title: "Security Testing",
      description: "Integrate security testing into your CI/CD pipeline.",
      icon: BookOpen,
      link: "https:
      color: "text-pink-400"
    }
  ];

  const resources = [
    {
      title: "OWASP Top 10",
      description: "The standard awareness document for developers and web application security.",
      link: "https:
      icon: FileText
    },
    {
      title: "OWASP Cheat Sheet Series",
      description: "Concise collection of high value information on specific application security topics.",
      link: "https:
      icon: Code
    },
    {
      title: "SANS Security Resources",
      description: "Information security training, certification, and research.",
      link: "https:
      icon: GraduationCap
    }
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center mb-2">
        <div className="p-3 rounded-full bg-accent-DEFAULT/10 mr-4">
          <GraduationCap className="h-8 w-8 text-accent-DEFAULT" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-text-primary tracking-tight">Security Training</h1>
          <p className="text-text-secondary mt-1">Learn best practices and improve your security posture</p>
        </div>
      </div>

      <div className="card p-8">
        <h2 className="text-2xl font-bold text-text-primary mb-6 flex items-center">
          <BookOpen className="mr-3 h-6 w-6 text-accent-DEFAULT" />
          Top 5 AppSec Best Practices
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {bestPractices.map((practice, index) => (
            <div
              key={practice.id}
              className="bg-secondary/50 p-6 rounded-xl border border-highlight hover:border-accent-DEFAULT/50 hover:bg-secondary-light transition-all duration-300 group hover:-translate-y-1 shadow-lg"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start">
                <div className={`p-3 rounded-lg bg-primary-light border border-highlight mr-4 group-hover:scale-110 transition-transform duration-300`}>
                  <practice.icon className={`w-6 h-6 ${practice.color}`} />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-lg text-text-primary group-hover:text-accent-DEFAULT transition-colors">{practice.title}</h3>
                  <p className="text-text-secondary mt-2 text-sm leading-relaxed">{practice.description}</p>
                  <a
                    href={practice.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center mt-4 text-sm font-medium text-accent-DEFAULT hover:text-accent-DEFAULT/80 transition-colors"
                  >
                    Learn more <ExternalLink className="ml-1 h-3 w-3" />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {resources.map((resource, index) => (
          <a
            key={index}
            href={resource.link}
            target="_blank"
            rel="noopener noreferrer"
            className="card p-6 hover:border-accent-DEFAULT/50 transition-all duration-300 group hover:-translate-y-1 cursor-pointer"
          >
            <div className="flex items-center mb-4">
              <div className="p-2 rounded-lg bg-accent-DEFAULT/10 text-accent-DEFAULT mr-3 group-hover:bg-accent-DEFAULT group-hover:text-primary transition-colors">
                <resource.icon className="h-5 w-5" />
              </div>
              <h3 className="font-bold text-text-primary group-hover:text-accent-DEFAULT transition-colors">{resource.title}</h3>
            </div>
            <p className="text-text-secondary text-sm">{resource.description}</p>
          </a>
        ))}
      </div>
    </div>
  );
}