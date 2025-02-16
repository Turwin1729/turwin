import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';

const HomeContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
`;

const InputGroup = styled.div`
  display: flex;
  gap: 12px;
  align-items: center;
`;

const FileButton = styled(motion.button)`
  background: ${props => props.theme.colors.transparent};
  color: ${props => props.theme.colors.accent};
  padding: 12px;
  border-radius: ${props => props.theme.borderRadius};
  position: relative;

  &:hover {
    background: rgba(46, 64, 83, 0.9);
  }
`;

const Input = styled.input`
  background: ${props => props.theme.colors.darkGray};
  color: white;
  padding: 12px 16px;
  border-radius: ${props => props.theme.borderRadius};
  border: 2px solid transparent;
  width: 300px;
  font-size: 16px;

  &:focus {
    border-color: ${props => props.theme.colors.accent};
    outline: none;
  }

  &::placeholder {
    color: ${props => props.theme.colors.secondary};
    opacity: 0.5;
  }
`;

const SubmitButton = styled(motion.button)`
  background: ${props => props.theme.colors.accent};
  color: white;
  padding: 12px 24px;
  border-radius: ${props => props.theme.borderRadius};
  font-weight: 600;
  font-size: 18px;

  &:hover {
    filter: brightness(1.1);
  }
`;

const Tooltip = styled(motion.div)`
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: ${props => props.theme.colors.darkNavy};
  color: ${props => props.theme.colors.secondary};
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
  white-space: nowrap;
  pointer-events: none;
  margin-bottom: 8px;
`;

const MessageContainer = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: #343541;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const Message = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  background: #444654;
`;

const FileIcon = styled.div`
  width: 40px;
  height: 40px;
  background: #2196f3;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
`;

const FileInfo = styled.div`
  display: flex;
  flex-direction: column;
`;

const FileName = styled.div`
  color: #E0E0E0;
  font-size: 16px;
  font-weight: 500;
`;

const FileType = styled.div`
  color: #9CA3AF;
  font-size: 14px;
`;

const CloseButton = styled.button`
  position: absolute;
  top: 8px;
  right: 8px;
  background: none;
  border: none;
  color: #9CA3AF;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
  }
`;

const HomePage = () => {
  const navigate = useNavigate();
  const [showTooltip, setShowTooltip] = useState(false);
  const [website, setWebsite] = useState('');
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && (file.type === 'application/json' || file.type === 'application/xml')) {
      setSelectedFile(file);
      // Here you would typically send the file to your backend for parsing
      // For now, we'll just store it in state
    }
  };

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleSubmit = () => {
    if (website && selectedFile) {
      navigate('/visualization', { state: { website } });
    }
  };

  const clearSelectedFile = () => {
    setSelectedFile(null);
  };

  return (
    <>
      <AnimatePresence>
        {selectedFile && (
          <MessageContainer
            as={motion.div}
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Message>
              <FileIcon>
                <span>📄</span>
              </FileIcon>
              <FileInfo>
                <FileName>{selectedFile.name}</FileName>
                <FileType>File</FileType>
              </FileInfo>
              <CloseButton onClick={clearSelectedFile}>×</CloseButton>
            </Message>
          </MessageContainer>
        )}
      </AnimatePresence>
      <HomeContainer style={{ marginTop: selectedFile ? '80px' : '0' }}>
        <InputGroup>
          <FileButton
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleFileButtonClick}
          >
            +
            {showTooltip && (
              <Tooltip
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                Please attach the input website's OpenAI specification file.
              </Tooltip>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.xml"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
          </FileButton>

          <Input
            placeholder="turwinmc.com"
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
          />

          <SubmitButton
            onClick={handleSubmit}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            →
          </SubmitButton>
        </InputGroup>
      </HomeContainer>
    </>
  );
};

export default HomePage;
