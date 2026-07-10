import { Ionicons } from '@expo/vector-icons';
import { ReactNode, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { ActionButton } from '@/components/ActionButton';
import { colors, radii, spacing, typography } from '@/theme/tokens';

interface AuthFormValues {
  email: string;
  password: string;
}

interface AuthFormProps {
  mode: 'sign-in' | 'sign-up';
  disabled?: boolean;
  error?: string | null;
  footer?: ReactNode;
  isSubmitting?: boolean;
  message?: string | null;
  onSubmit(values: AuthFormValues): void;
}

const submitLabels = {
  'sign-in': 'Sign in',
  'sign-up': 'Create account',
} as const;

const submittingLabels = {
  'sign-in': 'Signing in...',
  'sign-up': 'Creating...',
} as const;

export function AuthForm({
  mode,
  disabled = false,
  error,
  footer,
  isSubmitting = false,
  message,
  onSubmit,
}: AuthFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);

  const trimmedEmail = email.trim();
  const canSubmit = useMemo(
    () => trimmedEmail.includes('@') && password.length >= 6 && !disabled && !isSubmitting,
    [disabled, isSubmitting, password.length, trimmedEmail],
  );

  function handleSubmit() {
    if (!canSubmit) {
      return;
    }

    onSubmit({ email: trimmedEmail, password });
  }

  return (
    <View style={styles.panel}>
      <View style={styles.field}>
        <Text style={styles.label}>Email</Text>
        <TextInput
          accessibilityLabel="Email"
          autoCapitalize="none"
          autoComplete="email"
          autoCorrect={false}
          inputMode="email"
          keyboardType="email-address"
          onChangeText={setEmail}
          onSubmitEditing={handleSubmit}
          placeholder="you@example.com"
          placeholderTextColor={colors.muted}
          returnKeyType="next"
          style={styles.input}
          textContentType="emailAddress"
          value={email}
        />
      </View>

      <View style={styles.field}>
        <Text style={styles.label}>Password</Text>
        <View style={styles.passwordRow}>
          <TextInput
            accessibilityLabel="Password"
            autoCapitalize="none"
            autoComplete={mode === 'sign-in' ? 'current-password' : 'new-password'}
            onChangeText={setPassword}
            onSubmitEditing={handleSubmit}
            placeholder={mode === 'sign-up' ? 'At least 6 characters' : 'Password'}
            placeholderTextColor={colors.muted}
            returnKeyType="go"
            secureTextEntry={!isPasswordVisible}
            style={styles.passwordInput}
            textContentType={mode === 'sign-in' ? 'password' : 'newPassword'}
            value={password}
          />
          <Pressable
            accessibilityLabel={isPasswordVisible ? 'Hide password' : 'Show password'}
            accessibilityRole="button"
            hitSlop={10}
            onPress={() => setIsPasswordVisible((current) => !current)}
            style={styles.iconButton}>
            <Ionicons
              color={colors.muted}
              name={isPasswordVisible ? 'eye-off-outline' : 'eye-outline'}
              size={22}
            />
          </Pressable>
        </View>
      </View>

      {error ? <Text style={styles.errorText}>{error}</Text> : null}
      {message ? <Text style={styles.successText}>{message}</Text> : null}

      <ActionButton
        disabled={!canSubmit}
        label={isSubmitting ? submittingLabels[mode] : submitLabels[mode]}
        onPress={handleSubmit}
      />

      {footer ? <View style={styles.footer}>{footer}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  field: {
    gap: spacing.xs,
  },
  label: {
    color: colors.muted,
    fontSize: typography.caption,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  input: {
    backgroundColor: colors.canvas,
    borderColor: colors.border,
    borderRadius: radii.md,
    borderWidth: 1,
    color: colors.text,
    fontSize: 16,
    minHeight: 50,
    paddingHorizontal: spacing.md,
  },
  passwordRow: {
    alignItems: 'center',
    backgroundColor: colors.canvas,
    borderColor: colors.border,
    borderRadius: radii.md,
    borderWidth: 1,
    flexDirection: 'row',
    minHeight: 50,
  },
  passwordInput: {
    color: colors.text,
    flex: 1,
    fontSize: 16,
    minHeight: 50,
    paddingHorizontal: spacing.md,
  },
  iconButton: {
    alignItems: 'center',
    height: 50,
    justifyContent: 'center',
    width: 48,
  },
  errorText: {
    color: colors.danger,
    fontSize: typography.caption,
    lineHeight: 18,
  },
  successText: {
    color: colors.success,
    fontSize: typography.caption,
    lineHeight: 18,
  },
  footer: {
    alignItems: 'center',
    gap: spacing.xs,
  },
});
