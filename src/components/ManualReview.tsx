import { useState } from 'react';
import { Check, X, MessageSquare, AlertTriangle } from 'lucide-react';

interface ManualReviewProps {
  findingId: string;
  initialStatus: string;
  onReviewSubmit: (data: any) => void;
}

export default function ManualReview({ findingId, initialStatus, onReviewSubmit }: ManualReviewProps) {
  const [status, setStatus] = useState(initialStatus || 'OPEN');
  const [comment, setComment] = useState('');
  const [reviewer, setReviewer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const statusOptions = [
    { value: 'OPEN', label: 'Open', icon: AlertTriangle, color: 'text-yellow-500' },
    { value: 'IN_PROGRESS', label: 'In Progress', icon: MessageSquare, color: 'text-blue-500' },
    { value: 'FIXED', label: 'Fixed', icon: Check, color: 'text-green-500' },
    { value: 'FALSE_POSITIVE', label: 'False Positive', icon: X, color: 'text-gray-500' }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const reviewData = {
        status,
        comment,
        reviewer: reviewer || 'Anonymous',
        timestamp: new Date().toISOString()
      };

      await onReviewSubmit(reviewData);
      setComment('');
      setIsSubmitting(false);
    } catch (error) {
      console.error('Error submitting review:', error);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-secondary p-4 rounded-lg border border-highlight">
      <h3 className="text-lg font-semibold mb-4">Manual Review</h3>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Status</label>
          <div className="flex space-x-2">
            {statusOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setStatus(option.value)}
                className={`flex items-center px-3 py-2 rounded-md ${
                  status === option.value 
                    ? 'bg-accent text-white' 
                    : 'bg-secondary-light hover:bg-secondary-dark'
                }`}
              >
                <option.icon className={`w-4 h-4 mr-1 ${option.color}`} />
                {option.label}
              </button>
            ))}
          </div>
        </div>
        
        <div>
          <label htmlFor="reviewer" className="block text-sm font-medium mb-1">Reviewer</label>
          <input
            id="reviewer"
            type="text"
            value={reviewer}
            onChange={(e) => setReviewer(e.target.value)}
            placeholder="Your name"
            className="w-full px-3 py-2 bg-secondary-light rounded-md border border-highlight"
          />
        </div>
        
        <div>
          <label htmlFor="comment" className="block text-sm font-medium mb-1">Comment</label>
          <textarea
            id="comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Add your review comments here..."
            rows={4}
            className="w-full px-3 py-2 bg-secondary-light rounded-md border border-highlight"
          />
        </div>
        
        <button
          type="submit"
          disabled={isSubmitting || !comment}
          className={`px-4 py-2 rounded-md ${
            isSubmitting || !comment
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-accent hover:bg-accent-dark'
          } text-white font-medium`}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Review'}
        </button>
      </form>
    </div>
  );
}