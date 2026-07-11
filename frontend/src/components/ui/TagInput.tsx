import { useState, KeyboardEvent } from 'react';
import { X } from 'lucide-react';

interface TagInputProps {
  tags: string[];
  setTags: (tags: string[]) => void;
  placeholder?: string;
  required?: boolean;
  label?: string;
  error?: boolean;
  errorMessage?: string;
}

const TagInput: React.FC<TagInputProps> = ({
  tags,
  setTags,
  placeholder = 'Type and press Enter or comma to add',
  required = false,
  label,
  error = false,
  errorMessage
}) => {
  const [inputValue, setInputValue] = useState('');

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag();
    } else if (e.key === 'Backspace' && inputValue === '' && tags.length > 0) {
      // Remove last tag when input is empty and backspace is pressed
      removeTag(tags.length - 1);
    }
  };

  const addTag = () => {
    const trimmedValue = inputValue.trim();
    
    // Ignore empty values
    if (!trimmedValue) {
      setInputValue('');
      return;
    }

    // Prevent duplicate entries (case-insensitive)
    const isDuplicate = tags.some(
      tag => tag.toLowerCase() === trimmedValue.toLowerCase()
    );

    if (isDuplicate) {
      setInputValue('');
      return;
    }

    // Add the new tag
    setTags([...tags, trimmedValue]);
    setInputValue('');
  };

  const removeTag = (indexToRemove: number) => {
    setTags(tags.filter((_, index) => index !== indexToRemove));
  };

  return (
    <div className="space-y-1">
      {label && (
        <label className="text-sm font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div
        className={`flex flex-wrap gap-2 p-2 border rounded-lg focus-within:ring-2 focus-within:ring-indigo-500 outline-none bg-white min-h-[44px] ${
          error ? 'border-red-500' : 'border-gray-300'
        }`}
      >
        {tags.map((tag, index) => (
          <span
            key={index}
            className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-sm font-medium"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(index)}
              className="hover:text-indigo-900 focus:outline-none"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={addTag}
          placeholder={tags.length === 0 ? placeholder : ''}
          className="flex-1 min-w-[120px] outline-none bg-transparent text-sm py-1"
        />
      </div>
      {error && errorMessage && (
        <p className="text-red-500 text-xs mt-1">{errorMessage}</p>
      )}
    </div>
  );
};

export default TagInput;
