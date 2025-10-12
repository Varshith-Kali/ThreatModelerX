import { BookOpen, Shield, Code, Lock, AlertTriangle } from 'lucide-react';

export default function TrainingSection() {
  const bestPractices = [
    {
      id: 1,
      title: "Input Validation",
      description: "Always validate and sanitize all user inputs to prevent injection attacks.",
      icon: Shield,
      link: "https://owasp.org/www-project-top-ten/2017/A1_2017-Injection"
    },
    {
      id: 2,
      title: "Authentication & Authorization",
      description: "Implement strong authentication and proper authorization checks.",
      icon: Lock,
      link: "https://owasp.org/www-project-top-ten/2017/A2_2017-Broken_Authentication"
    },
    {
      id: 3,
      title: "Secure Data Storage",
      description: "Encrypt sensitive data at rest and in transit. Never store secrets in code.",
      icon: Code,
      link: "https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure"
    },
    {
      id: 4,
      title: "Dependency Management",
      description: "Regularly update dependencies and scan for vulnerabilities.",
      icon: AlertTriangle,
      link: "https://owasp.org/www-project-top-ten/2017/A9_2017-Using_Components_with_Known_Vulnerabilities"
    },
    {
      id: 5,
      title: "Security Testing",
      description: "Integrate security testing into your CI/CD pipeline.",
      icon: BookOpen,
      link: "https://owasp.org/www-project-top-ten/2017/A6_2017-Security_Misconfiguration"
    }
  ];

  return (
    <div className="bg-secondary rounded-xl p-8 border border-highlight shadow-lg">
      <h2 className="text-2xl font-bold text-accent mb-6 flex items-center">
        <BookOpen className="mr-2" /> Top 5 AppSec Best Practices
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {bestPractices.map((practice) => (
          <div 
            key={practice.id} 
            className="bg-secondary-light p-4 rounded-lg border border-highlight hover:shadow-md transition-shadow"
          >
            <div className="flex items-start">
              <div className="bg-accent bg-opacity-10 p-2 rounded-full mr-3">
                <practice.icon className="w-6 h-6 text-accent" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">{practice.title}</h3>
                <p className="text-text-secondary mt-1">{practice.description}</p>
                <a 
                  href={practice.link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-accent hover:underline text-sm mt-2 inline-block"
                >
                  Learn more →
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-8 p-4 bg-accent bg-opacity-10 rounded-lg">
        <h3 className="font-semibold mb-2">Additional Resources</h3>
        <ul className="list-disc list-inside space-y-1 text-text-secondary">
          <li>
            <a 
              href="https://owasp.org/www-project-top-ten/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              OWASP Top 10
            </a>
          </li>
          <li>
            <a 
              href="https://cheatsheetseries.owasp.org/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              OWASP Cheat Sheet Series
            </a>
          </li>
          <li>
            <a 
              href="https://www.sans.org/security-resources/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              SANS Security Resources
            </a>
          </li>
        </ul>
      </div>
    </div>
  );
}